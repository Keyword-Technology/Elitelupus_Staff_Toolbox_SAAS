import logging
import re

import a2s
from a2s import BrokenMessageError
from apps.staff.models import ServerSession, StaffRoster
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.utils import timezone

from .models import GameServer, ServerPlayer, ServerStatusLog

logger = logging.getLogger(__name__)


def normalize_name(name):
    """
    Normalize a player name by removing numbers from start/end for matching.
    Examples:
        'Cloudyman2' -> 'cloudyman'
        '2Cloudyman' -> 'cloudyman'
        'Admin123' -> 'admin'
        'Player' -> 'player'
    """
    # Convert to lowercase
    normalized = name.lower().strip()
    # Remove numbers from the start
    normalized = re.sub(r'^\d+', '', normalized)
    # Remove numbers from the end
    normalized = re.sub(r'\d+$', '', normalized)
    return normalized


def find_matching_staff(player_name, staff_roster_dict):
    """
    Find a matching staff member for a player name.
    
    The staff_roster_dict should contain both roster names and Steam names
    (when available) as keys, mapped to their StaffRoster objects.
    
    Matching logic:
    1. Direct case-insensitive match against roster name or Steam name
    2. Normalized match (numbers removed from start/end) for flexibility
    
    Args:
        player_name: The player name from the server
        staff_roster_dict: Dictionary of lowercase staff names (roster + steam) -> StaffRoster objects
    
    Returns:
        StaffRoster object if match found, None otherwise
    """
    # Direct match first (fastest)
    normalized_player = player_name.lower().strip()
    if normalized_player in staff_roster_dict:
        return staff_roster_dict[normalized_player]
    
    # Try normalized match (remove numbers)
    normalized_player = normalize_name(player_name)
    
    # Check if normalized player name matches any normalized staff name
    for staff_key, staff_entry in staff_roster_dict.items():
        if normalize_name(staff_key) == normalized_player:
            return staff_entry
    
    return None


class ServerQueryService:
    """Service for querying game server status."""
    
    def query_server(self, server):
        """Query a single server for its status and players."""
        try:
            address = (server.ip_address, server.port)
            
            # Query server info
            info = a2s.info(address, timeout=5)
            
            # Try to query players
            players = []
            query_method = "none"
            
            try:
                players = a2s.players(address, timeout=5)
                query_method = "a2s"
                logger.debug(f"Successfully queried {len(players)} players using python-a2s")
            except (OSError, BrokenMessageError) as e:
                # Handle bz2 decompression errors or other query failures
                # This is a known issue with some GMod servers sending corrupted compressed data
                logger.warning(f"Failed to query players for {server.name}: {type(e).__name__}: {e}")
                logger.info(f"Server will still be marked as online based on info query, but detailed player list unavailable")
                
                else:
                    raise  # Re-raise if it's a different OSError
            
            # Update server record
            server.server_name = info.server_name
            server.map_name = info.map_name
            server.max_players = info.max_players
            server.current_players = info.player_count
            server.is_online = True
            server.last_query = timezone.now()
            server.last_successful_query = timezone.now()
            server.save()
            
            # Update players (may be empty list if player query failed)
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
        
        # Get staff list for matching (excluding builders if setting enabled)
        # Build multiple lookup dictionaries for different name sources:
        # 1. Roster name (from Google Sheets)
        # 2. Steam name (from Steam API, synced periodically)
        from django.db.models import Q
        
        staff_queryset = StaffRoster.objects.filter(is_active=True).select_related('staff')
        
        # Exclude builders if system setting is enabled
        try:
            from apps.system_settings.models import SystemSetting
            if SystemSetting.exclude_builders():
                staff_queryset = staff_queryset.exclude(Q(rank__icontains='builder'))
        except Exception:
            # Setting doesn't exist yet or database error - skip filtering
            pass
        
        staff_roster = {}
        for entry in staff_queryset:
            # Key by roster name (lowercase)
            staff_roster[entry.name.lower()] = entry
            
            # Also key by Steam name if available (lowercase)
            if entry.staff and entry.staff.steam_name:
                steam_name_lower = entry.staff.steam_name.lower()
                # Only add if not already present (roster name takes priority)
                if steam_name_lower not in staff_roster:
                    staff_roster[steam_name_lower] = entry
        
        # Track new staff on server
        new_staff = {}
        
        for player in players:
            # Use flexible matching function
            staff_entry = find_matching_staff(player.name, staff_roster)
            is_staff = staff_entry is not None
            
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
        
        # Track session changes and broadcast staff online status
        self._track_session_changes(server, current_staff, new_staff)
    
    def _track_session_changes(self, server, old_staff, new_staff):
        """Track staff join/leave events and update sessions."""
        from apps.staff.consumers import broadcast_staff_online_change
        
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
                
                # Update staff roster online status and last_seen
                staff_entry = active_session.staff
                
                # Always update last_seen when staff leaves
                staff_entry.last_seen = now
                
                # Check if staff is still on another server
                still_online = ServerSession.objects.filter(
                    staff=staff_entry,
                    leave_time__isnull=True
                ).exists()
                
                # Save last_seen timestamp
                staff_entry.save(update_fields=['last_seen'])
                    
                # Broadcast staff went offline from this server
                if not still_online:
                    try:
                        broadcast_staff_online_change(
                            staff_id=staff_entry.steam_id,
                            is_online=False,
                            server_name=None,
                            server_id=None
                        )
                    except Exception as e:
                        logger.warning(f"Could not broadcast staff offline: {e}")
        
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
                # Create new session - use staff_entry.staff (Staff object), not staff_entry (StaffRoster)
                try:
                    ServerSession.objects.create(
                        staff=staff_entry.staff,
                        server=server,
                        join_time=now,
                        steam_id=steam_id,
                        player_name=staff_entry.name
                    )
                    logger.info(f"Started session for {staff_entry.name} on {server.name}")
                except Exception as e:
                    logger.error(f"Failed to create session for {staff_entry.name}: {e}")
                    continue
                
                # Broadcast staff came online
                try:
                    broadcast_staff_online_change(
                        staff_id=staff_entry.staff.steam_id,
                        is_online=True,
                        server_name=server.name,
                        server_id=server.id
                    )
                except Exception as e:
                    logger.warning(f"Could not broadcast staff online: {e}")
        
        # Also check for staff who are online but don't have active sessions
        # This handles edge cases like system restarts or missed join events
        for steam_id, staff_entry in new_staff.items():
            existing_session = ServerSession.objects.filter(
                server=server,
                steam_id=steam_id,
                leave_time__isnull=True
            ).first()
            
            if not existing_session:
                # Staff is online but has no active session - create one
                try:
                    ServerSession.objects.create(
                        staff=staff_entry.staff,
                        server=server,
                        join_time=now,
                        steam_id=steam_id,
                        player_name=staff_entry.name
                    )
                    logger.info(f"Created missing session for {staff_entry.name} on {server.name} (recovery)")
                except Exception as e:
                    logger.error(f"Failed to create recovery session for {staff_entry.name}: {e}")
        
        # Close any orphaned sessions - active sessions for staff who are NOT currently on this server
        # This handles edge cases where staff left but their session wasn't properly closed
        online_steam_ids = set(new_staff.keys())
        orphaned_sessions = ServerSession.objects.filter(
            server=server,
            leave_time__isnull=True
        ).exclude(steam_id__in=online_steam_ids)
        
        for session in orphaned_sessions:
            session.leave_time = now
            session.calculate_duration()
            session.save()
            logger.info(f"Closed orphaned session for {session.player_name} on {server.name} (cleanup)")
            
            # Update last_seen for the staff member
            try:
                session.staff.last_seen = now
                session.staff.save(update_fields=['last_seen'])
            except Exception as e:
                logger.warning(f"Could not update last_seen for {session.player_name}: {e}")
    
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
        
        # Build staff roster dict for matching
        staff_roster = {
            entry.name.lower(): entry 
            for entry in all_staff
        }
        
        # Track which staff are found online (by their database object)
        online_staff_ids = set()
        
        for server in servers:
            server_players = ServerPlayer.objects.filter(
                server=server, is_staff=True
            )
            
            for player in server_players:
                # Find matching staff member
                staff_entry = find_matching_staff(player.name, staff_roster)
                
                if staff_entry:
                    online_staff_ids.add(staff_entry.id)
                    
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
            if staff.id not in online_staff_ids:
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
