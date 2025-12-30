import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model


class CounterConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time counter updates."""

    async def connect(self):
        self.user = self.scope['user']
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Join user's personal counter channel
        self.user_group = f"counters_{self.user.id}"
        await self.channel_layer.group_add(
            self.user_group,
            self.channel_name
        )
        
        # Join global leaderboard channel
        await self.channel_layer.group_add(
            "counters_leaderboard",
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial counter data
        await self.send_initial_data()

    async def disconnect(self, close_code):
        # Leave groups
        if hasattr(self, 'user_group'):
            await self.channel_layer.group_discard(
                self.user_group,
                self.channel_name
            )
        
        await self.channel_layer.group_discard(
            "counters_leaderboard",
            self.channel_name
        )

    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'update':
                counter_type = data.get('counter_type')
                update_action = data.get('update_action', 'increment')
                value = data.get('value', 1)
                
                if counter_type in ['sit', 'ticket']:
                    new_count = await self.update_counter(
                        counter_type, update_action, value
                    )
                    
                    # Broadcast to all user's devices
                    await self.channel_layer.group_send(
                        self.user_group,
                        {
                            'type': 'counter_update',
                            'counter_type': counter_type,
                            'count': new_count,
                            'user_id': self.user.id,
                            'username': self.user.username,
                        }
                    )
                    
                    # Broadcast to leaderboard
                    await self.channel_layer.group_send(
                        "counters_leaderboard",
                        {
                            'type': 'leaderboard_update',
                            'user_id': self.user.id,
                            'username': self.user.username,
                            'display_name': self.user.display_name or self.user.username,
                            'counter_type': counter_type,
                            'count': new_count,
                        }
                    )
            
            elif action == 'get_leaderboard':
                leaderboard = await self.get_leaderboard()
                await self.send(text_data=json.dumps({
                    'type': 'leaderboard',
                    'data': leaderboard
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))

    async def counter_update(self, event):
        """Handle counter update broadcast."""
        await self.send(text_data=json.dumps({
            'type': 'counter_update',
            'counter_type': event['counter_type'],
            'count': event['count'],
            'user_id': event['user_id'],
            'username': event['username'],
        }))

    async def leaderboard_update(self, event):
        """Handle leaderboard update broadcast."""
        await self.send(text_data=json.dumps({
            'type': 'leaderboard_update',
            'user_id': event['user_id'],
            'username': event['username'],
            'display_name': event['display_name'],
            'counter_type': event['counter_type'],
            'count': event['count'],
        }))

    @database_sync_to_async
    def send_initial_data(self):
        """Send initial counter data when connection is established."""
        from .models import Counter
        
        sit_counter = Counter.objects.filter(
            user=self.user, counter_type='sit', period_type='total'
        ).first()
        
        ticket_counter = Counter.objects.filter(
            user=self.user, counter_type='ticket', period_type='total'
        ).first()
        
        return {
            'sits': sit_counter.count if sit_counter else 0,
            'tickets': ticket_counter.count if ticket_counter else 0,
        }

    async def send_initial_data(self):
        """Send initial counter data."""
        data = await self._get_initial_data()
        await self.send(text_data=json.dumps({
            'type': 'initial_data',
            'data': data
        }))

    @database_sync_to_async
    def _get_initial_data(self):
        from .models import Counter
        
        sit_counter = Counter.objects.filter(
            user=self.user, counter_type='sit', period_type='total'
        ).first()
        
        ticket_counter = Counter.objects.filter(
            user=self.user, counter_type='ticket', period_type='total'
        ).first()
        
        return {
            'sits': sit_counter.count if sit_counter else 0,
            'tickets': ticket_counter.count if ticket_counter else 0,
        }

    @database_sync_to_async
    def update_counter(self, counter_type, action, value):
        from .models import Counter, CounterHistory
        
        counter, _ = Counter.objects.get_or_create(
            user=self.user,
            counter_type=counter_type,
            period_type='total',
            defaults={'count': 0}
        )
        
        old_value = counter.count
        
        if action == 'increment':
            counter.count += value
        elif action == 'decrement':
            counter.count = max(0, counter.count - value)
        elif action == 'set':
            counter.count = max(0, value)
        elif action == 'reset':
            counter.count = 0
        
        counter.save()
        
        # Log history
        CounterHistory.objects.create(
            user=self.user,
            counter_type=counter_type,
            action=action,
            old_value=old_value,
            new_value=counter.count,
        )
        
        return counter.count

    @database_sync_to_async
    def get_leaderboard(self):
        from .models import Counter
        from django.db.models import Sum
        from django.db.models.functions import Coalesce
        
        User = get_user_model()
        users = User.objects.filter(is_active_staff=True)
        
        leaderboard = []
        for user in users:
            sit_count = Counter.objects.filter(
                user=user, counter_type='sit', period_type='total'
            ).aggregate(total=Coalesce(Sum('count'), 0))['total']
            
            ticket_count = Counter.objects.filter(
                user=user, counter_type='ticket', period_type='total'
            ).aggregate(total=Coalesce(Sum('count'), 0))['total']
            
            leaderboard.append({
                'user_id': user.id,
                'username': user.username,
                'display_name': user.display_name or user.username,
                'avatar_url': user.avatar_url,
                'role': user.role,
                'sit_count': sit_count,
                'ticket_count': ticket_count,
                'total_count': sit_count + ticket_count,
            })
        
        leaderboard.sort(key=lambda x: x['total_count'], reverse=True)
        return leaderboard
