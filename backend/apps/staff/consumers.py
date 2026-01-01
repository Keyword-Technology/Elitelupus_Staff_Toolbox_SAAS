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
        from .models import StaffRoster
        
        staff = StaffRoster.objects.filter(is_active=True).select_related('user')[:100]
        
        return {
            'total_active': StaffRoster.objects.filter(is_active=True).count(),
            'total_online': StaffRoster.objects.filter(is_active=True, is_online=True).count(),
            'total_on_loa': StaffRoster.objects.filter(is_active=True, is_on_loa=True).count(),
            'staff': [
                {
                    'id': s.id,
                    'name': s.name,
                    'role': s.role,
                    'role_color': s.role_color,
                    'is_online': s.is_online,
                    'server_name': s.server_name,
                    'server_id': s.server_id,
                    'discord_status': s.discord_status,
                    'is_on_loa': s.is_on_loa,
                }
                for s in staff
            ]
        }

    @database_sync_to_async
    def _get_online_staff(self):
        from .models import StaffRoster
        
        online = StaffRoster.objects.filter(is_active=True, is_online=True)
        
        return [
            {
                'id': s.id,
                'name': s.name,
                'role': s.role,
                'role_color': s.role_color,
                'server_name': s.server_name,
                'server_id': s.server_id,
            }
            for s in online
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
