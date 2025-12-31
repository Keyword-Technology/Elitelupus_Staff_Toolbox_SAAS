import logging

import a2s
from a2s import BrokenMessageError
from apps.staff.models import StaffRoster, ServerSession
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.utils import timezone

from .models import GameServer, ServerPlayer, ServerStatusLog

logger = logging.getLogger(__name__)


class ServerQueryService:
    """Service for querying game server status."""
    
    def query_server(self, server):
        """Query a single server for its status and players."""
        try:
            address = (server.ip_address, server.port)
            
            # Query server info
            info = a2s.info(address, timeout=5)
            players = a2s.players(address, timeout=5)
            
            # Update server record
            server.server_name = info.server_name
            server.map_name = info.map_name
            server.max_players = info.max_players
            server.current_players = info.player_count
            server.is_online = True
            server.last_query = timezone.now()
            server.last_successful_query = timezone.now()
            server.save()
            
            # Update players
            self._update_server_players(server, players)
            
            # Log status
            staff_count = ServerPlayer.objects.filter(
                server=server, is_staff=True
            ).count()
            
            ServerStatusLog.objects.create(
                server=server,
                player_count=info.player_count,
                staff_count=staff_count,
                is_online=True
            )
            
            return {
                'server_name': info.server_name,
                'map': info.map_name,
                'players': info.player_count,
                'max_players': info.max_players,
                'online': True,
            }
            
        except BrokenMessageError as e:
            # Invalid or partial UDP payload; typically means the server is unreachable, firewalled, or answering with a non-Source packet.
            logger.warning(f"Invalid A2S response from {server.name} ({server.ip_address}:{server.port}): {e}")
            return self._handle_server_error(server, f"Invalid data stream (A2S parse failed)")
        except Exception as e:
            logger.error(f"Error querying server {server.name}: {e}")
            return self._handle_server_error(server, str(e))
    def _handle_server_error(self, server, error_msg):
        server.is_online = False
        server.last_query = timezone.now()
        server.save()

        ServerStatusLog.objects.create(
            server=server,
            player_count=0,
            staff_count=0,
            is_online=False
        )

        return {
            'server_name': server.name,
            'online': False,
            'error': error_msg,
        }
    
    def _update_server_players(self, server, players):
        """Update player list for a server and track staff sessions."""
        # Get current staff on this server before clearing
        current_staff = {
            p.steam_id: p 
            for p in ServerPlayer.objects.filter(server=server, is_staff=True)
            if p.steam_id
        }
        
        # Clear old players
        ServerPlayer.objects.filter(server=server).delete()
        
        # Get staff list for matching
        staff_roster = {
            entry.name.lower(): entry 
            for entry in StaffRoster.objects.filter(is_active=True)
        }
        
        # Track new staff on server
        new_staff = {}
        
        for player in players:
            is_staff = player.name.lower() in staff_roster
            staff_entry = staff_roster.get(player.name.lower())
            
            steam_id = staff_entry.steam_id if staff_entry else None
            
            ServerPlayer.objects.create(
                server=server,
                name=player.name,
                score=player.score,
                duration=int(player.duration),
                is_staff=is_staff,
                staff_rank=staff_entry.rank if staff_entry else '',
                steam_id=steam_id,
            )
            
            if is_staff and steam_id:
                new_staff[steam_id] = staff_entry
        
        # Track session changes
        self._track_session_changes(server, current_staff, new_staff)
    
    def _track_session_changes(self, server, old_staff, new_staff):
        """Track staff join/leave events and update sessions."""
        now = timezone.now()
        
        # Find staff who left (were in old but not in new)
        left_staff = set(old_staff.keys()) - set(new_staff.keys())
        for steam_id in left_staff:
            # Close active session for this staff member
            active_session = ServerSession.objects.filter(
                server=server,
                steam_id=steam_id,
                leave_time__isnull=True
            ).first()
            
            if active_session:
                active_session.leave_time = now
                active_session.calculate_duration()
                active_session.save()
                logger.info(f"Closed session for {active_session.staff.name} on {server.name}")
        
        # Find staff who joined (in new but not in old)
        joined_staff = set(new_staff.keys()) - set(old_staff.keys())
        for steam_id in joined_staff:
            staff_entry = new_staff[steam_id]
            
            # Check if there's already an active session (shouldn't happen, but safety check)
            existing_session = ServerSession.objects.filter(
                server=server,
                steam_id=steam_id,
                leave_time__isnull=True
            ).first()
            
            if not existing_session:
                # Create new session
                ServerSession.objects.create(
                    staff=staff_entry,
                    server=server,
                    join_time=now,
                    steam_id=steam_id,
                    player_name=staff_entry.name
                )
                logger.info(f"Started session for {staff_entry.name} on {server.name}")
    
    def query_all_servers(self):
        """Query all active servers and return a list payload safe for WebSocket serialization."""
        servers = GameServer.objects.filter(is_active=True)
        results = []
        
        for server in servers:
            status = self.query_server(server)

            # Build a JSON-serializable payload with string keys only (msgpack rejects int keys).
            server_name = server.server_name or server.name
            map_name = server.map_name or 'Unknown'
            results.append({
                'id': server.id,
                'name': server.name,
                'server_name': server_name,
                'map_name': map_name,
                'current_players': server.current_players,
                'max_players': server.max_players,
                'is_online': server.is_online,
                'staff_online': ServerPlayer.objects.filter(server=server, is_staff=True).count(),
                'last_query': server.last_query.isoformat() if server.last_query else None,
                'error': status.get('error'),
            })
        
        # Broadcast update
        self._broadcast_server_update(results)
        
        return results
    
    def _broadcast_server_update(self, results):
        """Broadcast server status update via WebSocket."""
        channel_layer = get_channel_layer()
        
        async_to_sync(channel_layer.group_send)(
            "server_status",
            {
                'type': 'status_update',
                'data': results
            }
        )
    
    def get_staff_distribution(self):
        """Get staff distribution across servers."""
        servers = GameServer.objects.filter(is_active=True)
        
        distribution = {
            'server_1': [],
            'server_2': [],
            'offline': [],
        }
        
        # Get all active staff
        all_staff = list(StaffRoster.objects.filter(is_active=True))
        online_staff_names = set()
        
        for server in servers:
            server_players = ServerPlayer.objects.filter(
                server=server, is_staff=True
            )
            
            for player in server_players:
                online_staff_names.add(player.name.lower())
                
                staff_data = {
                    'name': player.name,
                    'rank': player.staff_rank,
                    'duration': player.duration_formatted,
                    'server': server.name,
                }
                
                if server.display_order == 0:
                    distribution['server_1'].append(staff_data)
                else:
                    distribution['server_2'].append(staff_data)
        
        # Add offline staff
        for staff in all_staff:
            if staff.name.lower() not in online_staff_names:
                distribution['offline'].append({
                    'name': staff.name,
                    'rank': staff.rank,
                    'server': None,
                })
        
        return distribution


def initialize_default_servers():
    """Initialize default Elitelupus servers."""
    servers = [
        {
            'name': 'Elitelupus Server 1',
            'ip_address': settings.ELITE_SERVER_1[0],
            'port': settings.ELITE_SERVER_1[1],
            'display_order': 0,
        },
        {
            'name': 'Elitelupus Server 2',
            'ip_address': settings.ELITE_SERVER_2[0],
            'port': settings.ELITE_SERVER_2[1],
            'display_order': 1,
        },
    ]
    
    for server_data in servers:
        GameServer.objects.get_or_create(
            ip_address=server_data['ip_address'],
            port=server_data['port'],
            defaults=server_data
        )
