import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer


class StaffStatusConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time staff status updates."""

    async def connect(self):
        self.user = self.scope['user']
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Join staff status group
        await self.channel_layer.group_add(
            "staff_status",
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial data
        await self.send_initial_data()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            "staff_status",
            self.channel_name
        )

    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'refresh':
                # Send current staff data
                await self.send_initial_data()
            elif action == 'get_online':
                # Get only online staff
                online_staff = await self._get_online_staff()
                await self.send(text_data=json.dumps({
                    'type': 'online_staff',
                    'data': online_staff
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))

    async def staff_update(self, event):
        """Handle staff status update broadcast."""
        await self.send(text_data=json.dumps({
            'type': 'staff_update',
            'data': event['data']
        }))

    async def staff_online_change(self, event):
        """Handle staff online status change broadcast."""
        await self.send(text_data=json.dumps({
            'type': 'staff_online_change',
            'staff_id': event['staff_id'],
            'is_online': event['is_online'],
            'server_name': event.get('server_name'),
            'server_id': event.get('server_id'),
        }))

    async def staff_discord_status(self, event):
        """Handle staff Discord status update broadcast."""
        await self.send(text_data=json.dumps({
            'type': 'staff_discord_status',
            'staff_id': event['staff_id'],
            'discord_status': event['discord_status'],
            'discord_custom_status': event.get('discord_custom_status'),
            'discord_activity': event.get('discord_activity'),
        }))

    async def staff_roster_sync(self, event):
        """Handle staff roster sync completion broadcast."""
        await self.send(text_data=json.dumps({
            'type': 'staff_roster_sync',
            'records_updated': event['records_updated'],
            'status': event['status'],
        }))

    async def send_initial_data(self):
        """Send initial staff status data."""
        data = await self._get_staff_summary()
        await self.send(text_data=json.dumps({
            'type': 'initial_data',
            'data': data
        }))

    @database_sync_to_async
    def _get_staff_summary(self):
        from apps.servers.models import ServerPlayer

        from .models import Staff, StaffRoster
        
        staff = StaffRoster.objects.filter(is_active=True).select_related('staff')[:100]
        
        # Get all online staff steam_ids from ServerPlayer
        online_steam_ids = set(
            ServerPlayer.objects.filter(is_staff=True).values_list('steam_id', flat=True)
        )
        
        # Count online staff (those in roster with matching steam_id in ServerPlayer)
        total_online = sum(1 for s in staff if s.steam_id in online_steam_ids)
        
        # Count LOA staff
        total_on_loa = Staff.objects.filter(staff_status='loa').count()
        
        def get_server_info(steam_id):
            """Get server name and ID for a staff member."""
            player = ServerPlayer.objects.filter(steam_id=steam_id, is_staff=True).first()
            if player:
                return player.server.name, player.server.id
            return None, None
        
        staff_list = []
        for s in staff:
            is_online = s.steam_id in online_steam_ids
            server_name, server_id = get_server_info(s.steam_id) if is_online else (None, None)
            is_on_loa = s.staff.staff_status == 'loa' if hasattr(s, 'staff') else False
            
            staff_list.append({
                'id': s.id,
                'name': s.name,
                'role': s.rank,
                'role_color': s.rank_color,
                'is_online': is_online,
                'server_name': server_name,
                'server_id': server_id,
                'discord_status': s.discord_status,
                'is_on_loa': is_on_loa,
            })
        
        return {
            'total_active': StaffRoster.objects.filter(is_active=True).count(),
            'total_online': total_online,
            'total_on_loa': total_on_loa,
            'staff': staff_list
        }

    @database_sync_to_async
    def _get_online_staff(self):
        from apps.servers.models import ServerPlayer

        from .models import StaffRoster

        # Get all online staff steam_ids from ServerPlayer
        online_players = ServerPlayer.objects.filter(is_staff=True).select_related('server')
        online_steam_ids = {p.steam_id: p for p in online_players}
        
        # Get roster entries for online staff
        roster_entries = StaffRoster.objects.filter(
            is_active=True,
            staff_id__in=online_steam_ids.keys()
        ).select_related('staff')
        
        return [
            {
                'id': s.id,
                'name': s.name,
                'role': s.rank,
                'role_color': s.rank_color,
                'server_name': online_steam_ids[s.staff_id].server.name if s.staff_id in online_steam_ids else None,
                'server_id': online_steam_ids[s.staff_id].server.id if s.staff_id in online_steam_ids else None,
            }
            for s in roster_entries
        ]


# Helper function to broadcast staff updates from other parts of the app
def broadcast_staff_update(staff_data):
    """
    Broadcast a staff update to all connected clients.
    Call this from views/tasks when staff data changes.
    """
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer
    
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "staff_status",
        {
            'type': 'staff_update',
            'data': staff_data
        }
    )


def broadcast_staff_online_change(staff_id, is_online, server_name=None, server_id=None):
    """
    Broadcast when a staff member goes online/offline.
    """
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer
    
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "staff_status",
        {
            'type': 'staff_online_change',
            'staff_id': staff_id,
            'is_online': is_online,
            'server_name': server_name,
            'server_id': server_id,
        }
    )


def broadcast_staff_discord_status(staff_id, discord_status, custom_status=None, activity=None):
    """
    Broadcast when a staff member's Discord status changes.
    """
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer
    
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "staff_status",
        {
            'type': 'staff_discord_status',
            'staff_id': staff_id,
            'discord_status': discord_status,
            'discord_custom_status': custom_status,
            'discord_activity': activity,
        }
    )


def broadcast_roster_sync(records_updated, status='success'):
    """
    Broadcast when the staff roster has been synced.
    """
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer
    
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "staff_status",
        {
            'type': 'staff_roster_sync',
            'records_updated': records_updated,
            'status': status,
        }
    )
