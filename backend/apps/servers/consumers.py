import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class ServerStatusConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time server status updates."""

    async def connect(self):
        self.user = self.scope['user']
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Join server status group
        await self.channel_layer.group_add(
            "server_status",
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial data
        await self.send_initial_data()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            "server_status",
            self.channel_name
        )

    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'refresh':
                # Trigger server refresh
                result = await self.refresh_servers()
                await self.send(text_data=json.dumps({
                    'type': 'refresh_result',
                    'data': result
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))

    async def status_update(self, event):
        """Handle server status update broadcast."""
        await self.send(text_data=json.dumps({
            'type': 'status_update',
            'data': event['data']
        }))

    async def send_initial_data(self):
        """Send initial server status data."""
        data = await self._get_server_status()
        await self.send(text_data=json.dumps({
            'type': 'initial_data',
            'data': data
        }))

    @database_sync_to_async
    def _get_server_status(self):
        from .models import GameServer, ServerPlayer
        
        servers = GameServer.objects.filter(is_active=True)
        
        result = []
        for server in servers:
            staff_count = ServerPlayer.objects.filter(
                server=server, is_staff=True
            ).count()
            
            players = ServerPlayer.objects.filter(server=server)
            
            result.append({
                'id': server.id,
                'name': server.name,
                'server_name': server.server_name,
                'map_name': server.map_name,
                'current_players': server.current_players,
                'max_players': server.max_players,
                'is_online': server.is_online,
                'staff_online': staff_count,
                'players': [
                    {
                        'name': p.name,
                        'score': p.score,
                        'duration': p.duration_formatted,
                        'is_staff': p.is_staff,
                        'staff_rank': p.staff_rank,
                    }
                    for p in players
                ]
            })
        
        return result

    @database_sync_to_async
    def refresh_servers(self):
        from .services import ServerQueryService
        service = ServerQueryService()
        return service.query_all_servers()
