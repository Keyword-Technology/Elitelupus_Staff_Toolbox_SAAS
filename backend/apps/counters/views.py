from datetime import timedelta

from apps.utils import get_week_start
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models import Avg, Count, F, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (Counter, CounterHistory, CounterSnapshot, Sit, SitNote,
                     UserSitPreferences)
from .serializers import (CounterHistorySerializer, CounterSerializer,
                          CounterSnapshotSerializer, CounterStatsSerializer,
                          CounterUpdateSerializer, LeaderboardEntrySerializer,
                          SitCreateSerializer, SitListSerializer,
                          SitNoteCreateSerializer, SitNoteSerializer,
                          SitRecordingUploadSerializer, SitSerializer,
                          SitStatsSerializer, SitUpdateSerializer,
                          UserSitPreferencesSerializer)


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
        week_start = get_week_start(today)  # Saturday is reset day
        
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
        
        # Calculate net change for today (new_value - old_value is already signed correctly)
        today_sits = 0
        for entry in today_history.filter(counter_type='sit'):
            today_sits += (entry.new_value - entry.old_value)
        
        today_tickets = 0
        for entry in today_history.filter(counter_type='ticket'):
            today_tickets += (entry.new_value - entry.old_value)
        
        # Weekly counts - include both increment and decrement
        weekly_history = CounterHistory.objects.filter(
            user=user,
            timestamp__date__gte=week_start,
            action__in=['increment', 'decrement']
        )
        
        # Calculate net change for week (new_value - old_value is already signed correctly)
        weekly_sits = 0
        for entry in weekly_history.filter(counter_type='sit'):
            weekly_sits += (entry.new_value - entry.old_value)
        
        weekly_tickets = 0
        for entry in weekly_history.filter(counter_type='ticket'):
            weekly_tickets += (entry.new_value - entry.old_value)
        
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


class ResetWeeklySitCounterView(APIView):
    """Reset weekly sit counter for the current user."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        today = timezone.now().date()
        week_start = get_week_start(today)  # Saturday is reset day
        
        # Get all sit history entries for this week
        weekly_history = CounterHistory.objects.filter(
            user=user,
            counter_type='sit',
            timestamp__date__gte=week_start,
            action__in=['increment', 'decrement']
        )
        
        # Calculate the net change for the week
        weekly_sits = 0
        for entry in weekly_history:
            weekly_sits += (entry.new_value - entry.old_value)
        
        # If there are sits to reset, create a compensating entry
        if weekly_sits != 0:
            # Get current counter
            counter, _ = Counter.objects.get_or_create(
                user=user,
                counter_type='sit',
                period_type='total',
                defaults={'count': 0}
            )
            
            old_value = counter.count
            # Subtract the weekly sits from the total counter
            counter.count = max(0, counter.count - weekly_sits)
            counter.save()
            
            # Log the reset in history
            CounterHistory.objects.create(
                user=user,
                counter_type='sit',
                action='reset',
                old_value=old_value,
                new_value=counter.count,
                note=f'Weekly sit counter reset: -{weekly_sits} sits'
            )
            
            # Broadcast update via WebSocket
            self._broadcast_counter_update(user, 'sit', counter.count)
        
        # Recalculate stats after reset
        weekly_history_after = CounterHistory.objects.filter(
            user=user,
            counter_type='sit',
            timestamp__date__gte=week_start,
            action__in=['increment', 'decrement']
        )
        
        new_weekly_sits = 0
        for entry in weekly_history_after:
            new_weekly_sits += (entry.new_value - entry.old_value)
        
        return Response({
            'message': 'Weekly sit counter reset successfully',
            'previous_weekly_sits': weekly_sits,
            'current_weekly_sits': new_weekly_sits,
            'total_sits': Counter.objects.filter(
                user=user, counter_type='sit', period_type='total'
            ).aggregate(total=Coalesce(Sum('count'), 0))['total']
        })
    
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


# ============================================================================
# SIT RECORDING SYSTEM VIEWS
# ============================================================================

class SitRecordingEnabledView(APIView):
    """Check if sit recording feature is enabled (system-wide and user preference)."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        from apps.system_settings.models import SystemSetting

        # Check system-wide settings using the static method
        # Main feature toggle - controls entire OCR/recording system visibility
        system_enabled = SystemSetting.get_setting_value('sit_recording_enabled', default=False)
        # OCR sub-feature toggle
        ocr_system_enabled = SystemSetting.get_setting_value('sit_recording_ocr_enabled', default=False)
        
        # Check user preference
        user_prefs, _ = UserSitPreferences.objects.get_or_create(user=request.user)
        
        return Response({
            'system_enabled': system_enabled,
            'ocr_system_enabled': ocr_system_enabled,
            'user_recording_enabled': user_prefs.recording_enabled,
            'user_ocr_enabled': user_prefs.ocr_enabled,
            'is_fully_enabled': system_enabled and user_prefs.recording_enabled,
        })


class UserSitPreferencesView(APIView):
    """Get and update user sit preferences."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        prefs, _ = UserSitPreferences.objects.get_or_create(user=request.user)
        return Response(UserSitPreferencesSerializer(prefs).data)
    
    def patch(self, request):
        prefs, _ = UserSitPreferences.objects.get_or_create(user=request.user)
        serializer = UserSitPreferencesSerializer(prefs, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class SitListCreateView(APIView):
    """List and create sits for the current user."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """List sits for current user with filtering."""
        queryset = Sit.objects.filter(staff=request.user)
        
        # Optional filters
        has_recording = request.query_params.get('has_recording')
        outcome = request.query_params.get('outcome')
        report_type = request.query_params.get('report_type')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        if has_recording is not None:
            queryset = queryset.filter(has_recording=has_recording.lower() == 'true')
        if outcome:
            queryset = queryset.filter(outcome=outcome)
        if report_type:
            queryset = queryset.filter(report_type=report_type)
        if date_from:
            queryset = queryset.filter(started_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(started_at__date__lte=date_to)
        
        # Pagination
        limit = int(request.query_params.get('limit', 50))
        offset = int(request.query_params.get('offset', 0))
        
        total = queryset.count()
        sits = queryset[offset:offset + limit]
        
        return Response({
            'total': total,
            'limit': limit,
            'offset': offset,
            'results': SitListSerializer(sits, many=True).data
        })
    
    def post(self, request):
        """Create a new sit (start recording)."""
        serializer = SitCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        sit = Sit.objects.create(
            staff=request.user,
            **serializer.validated_data
        )
        
        return Response(
            SitSerializer(sit, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )


class SitDetailView(APIView):
    """Get, update, or delete a specific sit."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self, sit_id, user):
        try:
            return Sit.objects.get(id=sit_id, staff=user)
        except Sit.DoesNotExist:
            return None
    
    def get(self, request, sit_id):
        sit = self.get_object(sit_id, request.user)
        if not sit:
            return Response({'error': 'Sit not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(SitSerializer(sit, context={'request': request}).data)
    
    def patch(self, request, sit_id):
        """Update sit details (e.g., complete the sit)."""
        sit = self.get_object(sit_id, request.user)
        if not sit:
            return Response({'error': 'Sit not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = SitUpdateSerializer(sit, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # If sit is being completed (ended_at is set), also increment counter
        if 'ended_at' in request.data and sit.ended_at:
            self._increment_sit_counter(request.user, sit)
        
        return Response(SitSerializer(sit, context={'request': request}).data)
    
    def delete(self, request, sit_id):
        sit = self.get_object(sit_id, request.user)
        if not sit:
            return Response({'error': 'Sit not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Delete associated recording files
        if sit.recording_file:
            sit.recording_file.delete()
        if sit.recording_thumbnail:
            sit.recording_thumbnail.delete()
        
        sit.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def _increment_sit_counter(self, user, sit):
        """Increment the legacy sit counter and link to the sit record."""
        counter, _ = Counter.objects.get_or_create(
            user=user,
            counter_type='sit',
            period_type='total',
            defaults={'count': 0}
        )
        
        old_value = counter.count
        counter.count += 1
        counter.save()
        
        # Create history entry
        history = CounterHistory.objects.create(
            user=user,
            counter_type='sit',
            action='increment',
            old_value=old_value,
            new_value=counter.count,
            note=f"Sit recording completed: {sit.reporter_name or 'Unknown'}"
        )
        
        # Link history to sit
        sit.counter_history = history
        sit.save()
        
        # Broadcast counter update via WebSocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"counters_{user.id}",
            {
                'type': 'counter_update',
                'counter_type': 'sit',
                'count': counter.count,
                'user_id': user.id,
                'username': user.username,
            }
        )


class SitRecordingUploadView(APIView):
    """Upload recording for a sit."""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request, sit_id):
        try:
            sit = Sit.objects.get(id=sit_id, staff=request.user)
        except Sit.DoesNotExist:
            return Response({'error': 'Sit not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = SitRecordingUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        recording = serializer.validated_data['recording']
        thumbnail = serializer.validated_data.get('thumbnail')
        
        # Save recording
        sit.recording_file = recording
        sit.recording_size_bytes = recording.size
        sit.has_recording = True
        
        if thumbnail:
            sit.recording_thumbnail = thumbnail
        
        sit.save()
        
        return Response({
            'message': 'Recording uploaded successfully',
            'recording_size_bytes': sit.recording_size_bytes,
        })


class SitNoteListCreateView(APIView):
    """List and create notes for a sit."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, sit_id):
        try:
            sit = Sit.objects.get(id=sit_id, staff=request.user)
        except Sit.DoesNotExist:
            return Response({'error': 'Sit not found'}, status=status.HTTP_404_NOT_FOUND)
        
        notes = sit.notes.all()
        return Response(SitNoteSerializer(notes, many=True).data)
    
    def post(self, request, sit_id):
        try:
            sit = Sit.objects.get(id=sit_id, staff=request.user)
        except Sit.DoesNotExist:
            return Response({'error': 'Sit not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = SitNoteCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        note = SitNote.objects.create(sit=sit, **serializer.validated_data)
        return Response(SitNoteSerializer(note).data, status=status.HTTP_201_CREATED)


class SitNoteDeleteView(APIView):
    """Delete a specific note."""
    permission_classes = [permissions.IsAuthenticated]
    
    def delete(self, request, sit_id, note_id):
        try:
            sit = Sit.objects.get(id=sit_id, staff=request.user)
            note = SitNote.objects.get(id=note_id, sit=sit)
        except (Sit.DoesNotExist, SitNote.DoesNotExist):
            return Response({'error': 'Note not found'}, status=status.HTTP_404_NOT_FOUND)
        
        note.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SitStatsView(APIView):
    """Get sit statistics for current user."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        today = timezone.now().date()
        week_start = get_week_start(today)  # Saturday is reset day
        month_start = today.replace(day=1)
        
        base_queryset = Sit.objects.filter(staff=user)
        
        # Total sits
        total_sits = base_queryset.count()
        
        # Today's sits
        today_sits = base_queryset.filter(started_at__date=today).count()
        
        # Weekly sits
        weekly_sits = base_queryset.filter(started_at__date__gte=week_start).count()
        
        # Monthly sits
        monthly_sits = base_queryset.filter(started_at__date__gte=month_start).count()
        
        # Sits with recording
        sits_with_recording = base_queryset.filter(has_recording=True).count()
        
        # Average duration
        avg_duration = base_queryset.filter(
            duration_seconds__isnull=False
        ).aggregate(avg=Avg('duration_seconds'))['avg'] or 0
        
        # Average rating
        avg_rating = base_queryset.filter(
            player_rating__isnull=False
        ).aggregate(avg=Avg('player_rating'))['avg']
        
        # Outcome breakdown
        outcome_breakdown = dict(
            base_queryset.exclude(outcome='').values('outcome')
            .annotate(count=Count('id'))
            .values_list('outcome', 'count')
        )
        
        # Detection method breakdown
        detection_breakdown = dict(
            base_queryset.values('detection_method')
            .annotate(count=Count('id'))
            .values_list('detection_method', 'count')
        )
        
        return Response({
            'total_sits': total_sits,
            'today_sits': today_sits,
            'weekly_sits': weekly_sits,
            'monthly_sits': monthly_sits,
            'sits_with_recording': sits_with_recording,
            'average_duration_seconds': avg_duration,
            'average_rating': avg_rating,
            'outcome_breakdown': outcome_breakdown,
            'detection_method_breakdown': detection_breakdown,
        })


class ActiveSitView(APIView):
    """Get the currently active (uncompleted) sit for the user."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Find sits that have started but not ended
        active_sit = Sit.objects.filter(
            staff=request.user,
            ended_at__isnull=True
        ).order_by('-started_at').first()
        
        if not active_sit:
            return Response({'active_sit': None})
        
        return Response({
            'active_sit': SitSerializer(active_sit, context={'request': request}).data
        })
