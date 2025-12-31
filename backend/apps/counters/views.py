from datetime import timedelta

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models import F, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Counter, CounterHistory, CounterSnapshot
from .serializers import (CounterHistorySerializer, CounterSerializer,
                          CounterSnapshotSerializer, CounterStatsSerializer,
                          CounterUpdateSerializer, LeaderboardEntrySerializer)


class MyCountersView(APIView):
    """Get and manage current user's counters."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Get or create counters
        sit_counter, _ = Counter.objects.get_or_create(
            user=user,
            counter_type='sit',
            period_type='total',
            defaults={'count': 0}
        )
        ticket_counter, _ = Counter.objects.get_or_create(
            user=user,
            counter_type='ticket',
            period_type='total',
            defaults={'count': 0}
        )
        
        return Response({
            'sits': CounterSerializer(sit_counter).data,
            'tickets': CounterSerializer(ticket_counter).data,
        })


class CounterUpdateView(APIView):
    """Update a specific counter."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, counter_type):
        if counter_type not in ['sit', 'ticket']:
            return Response(
                {'error': 'Invalid counter type'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = CounterUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        action = serializer.validated_data['action']
        value = serializer.validated_data.get('value', 1)
        note = serializer.validated_data.get('note', '')
        
        # Get or create counter
        counter, _ = Counter.objects.get_or_create(
            user=user,
            counter_type=counter_type,
            period_type='total',
            defaults={'count': 0}
        )
        
        old_value = counter.count
        
        # Apply action
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
            user=user,
            counter_type=counter_type,
            action=action,
            old_value=old_value,
            new_value=counter.count,
            note=note
        )
        
        # Broadcast update via WebSocket
        self._broadcast_counter_update(user, counter_type, counter.count)
        
        return Response(CounterSerializer(counter).data)
    
    def _broadcast_counter_update(self, user, counter_type, count):
        """Broadcast counter update to all connected clients."""
        channel_layer = get_channel_layer()
        
        # Send to user's personal channel
        async_to_sync(channel_layer.group_send)(
            f"counters_{user.id}",
            {
                'type': 'counter_update',
                'counter_type': counter_type,
                'count': count,
                'user_id': user.id,
                'username': user.username,
            }
        )
        
        # Send to global leaderboard channel
        async_to_sync(channel_layer.group_send)(
            "counters_leaderboard",
            {
                'type': 'leaderboard_update',
                'user_id': user.id,
                'username': user.username,
                'display_name': user.display_name or user.username,
                'counter_type': counter_type,
                'count': count,
            }
        )


class CounterStatsView(APIView):
    """Get counter statistics for current user."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        
        # Total counts
        total_sits = Counter.objects.filter(
            user=user, counter_type='sit', period_type='total'
        ).aggregate(total=Coalesce(Sum('count'), 0))['total']
        
        total_tickets = Counter.objects.filter(
            user=user, counter_type='ticket', period_type='total'
        ).aggregate(total=Coalesce(Sum('count'), 0))['total']
        
        # Today's counts (from history) - include both increment and decrement
        today_history = CounterHistory.objects.filter(
            user=user,
            timestamp__date=today,
            action__in=['increment', 'decrement']
        )
        
        # Calculate net change for today (increment adds, decrement subtracts)
        today_sits = 0
        for entry in today_history.filter(counter_type='sit'):
            if entry.action == 'increment':
                today_sits += (entry.new_value - entry.old_value)
            elif entry.action == 'decrement':
                today_sits -= (entry.new_value - entry.old_value)
        
        today_tickets = 0
        for entry in today_history.filter(counter_type='ticket'):
            if entry.action == 'increment':
                today_tickets += (entry.new_value - entry.old_value)
            elif entry.action == 'decrement':
                today_tickets -= (entry.new_value - entry.old_value)
        
        # Weekly counts - include both increment and decrement
        weekly_history = CounterHistory.objects.filter(
            user=user,
            timestamp__date__gte=week_start,
            action__in=['increment', 'decrement']
        )
        
        # Calculate net change for week
        weekly_sits = 0
        for entry in weekly_history.filter(counter_type='sit'):
            if entry.action == 'increment':
                weekly_sits += (entry.new_value - entry.old_value)
            elif entry.action == 'decrement':
                weekly_sits -= (entry.new_value - entry.old_value)
        
        weekly_tickets = 0
        for entry in weekly_history.filter(counter_type='ticket'):
            if entry.action == 'increment':
                weekly_tickets += (entry.new_value - entry.old_value)
            elif entry.action == 'decrement':
                weekly_tickets -= (entry.new_value - entry.old_value)
        
        return Response({
            'total_sits': total_sits,
            'total_tickets': total_tickets,
            'today_sits': today_sits,
            'today_tickets': today_tickets,
            'weekly_sits': weekly_sits,
            'weekly_tickets': weekly_tickets,
        })


class CounterHistoryView(generics.ListAPIView):
    """Get counter history for current user."""
    serializer_class = CounterHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        counter_type = self.request.query_params.get('type')
        
        queryset = CounterHistory.objects.filter(user=user)
        if counter_type:
            queryset = queryset.filter(counter_type=counter_type)
        
        return queryset[:100]  # Limit to last 100 entries


class LeaderboardView(APIView):
    """Get leaderboard of all staff counters."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        period = request.query_params.get('period', 'total')
        counter_type = request.query_params.get('type', 'all')
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Get all active staff users
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
                'role_color': user.role_color,
                'sit_count': sit_count,
                'ticket_count': ticket_count,
                'total_count': sit_count + ticket_count,
            })
        
        # Sort by total count
        if counter_type == 'sit':
            leaderboard.sort(key=lambda x: x['sit_count'], reverse=True)
        elif counter_type == 'ticket':
            leaderboard.sort(key=lambda x: x['ticket_count'], reverse=True)
        else:
            leaderboard.sort(key=lambda x: x['total_count'], reverse=True)
        
        return Response(leaderboard)
