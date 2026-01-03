import asyncio

from apps.accounts.permissions import IsManager, IsStaffManager, IsSysAdmin
from apps.utils import get_week_start
from django.conf import settings
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from .discord_service import get_bot_instance, sync_discord_statuses
from .models import (ServerSession, ServerSessionAggregate, Staff, StaffRoster,
                     StaffSyncLog)
from .serializers import (RolePrioritySerializer,
                          ServerSessionAggregateSerializer,
                          ServerSessionSerializer, StaffDetailsSerializer,
                          StaffRosterSerializer, StaffSyncLogSerializer)
from .services import StaffSyncService


class StaffRosterPagination(PageNumberPagination):
    """Custom pagination for staff roster with dynamic page size."""
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100


class StaffRosterListView(generics.ListAPIView):
    """List all staff members from roster."""
    serializer_class = StaffRosterSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StaffRosterPagination
    
    def get_queryset(self):
        from apps.system_settings.models import SystemSetting
        from django.db.models import Q

        # By default, show only active staff
        # Allow showing inactive/legacy staff with ?show_inactive=true
        show_inactive = self.request.query_params.get('show_inactive', 'false').lower() == 'true'
        
        if show_inactive:
            # Show all staff including inactive
            queryset = StaffRoster.objects.all()
        else:
            # Default: only active staff
            queryset = StaffRoster.objects.filter(is_active=True)
        
        # Exclude builders if system setting is enabled
        if SystemSetting.exclude_builders():
            queryset = queryset.exclude(Q(rank__icontains='builder'))
        
        # Filter by rank if provided
        rank = self.request.query_params.get('rank')
        if rank:
            queryset = queryset.filter(rank=rank)
        
        # Search by name or Steam ID (name is on related Staff model)
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(staff__name__icontains=search) |
                Q(staff__steam_id__icontains=search)
            )
        
        # Filter by role
        role = self.request.query_params.get('role')
        if role and role != 'all':
            queryset = queryset.filter(rank=role)
        
        # Handle ordering parameter
        ordering = self.request.query_params.get('ordering', 'rank_priority,staff__name')
        # Allow multiple ordering fields separated by comma
        order_fields = [field.strip() for field in ordering.split(',')]
        # Validate ordering fields to prevent SQL injection
        # Map 'name' to 'staff__name' for backwards compatibility
        field_mapping = {'name': 'staff__name', '-name': '-staff__name',
                        'steam_id': 'staff__steam_id', '-steam_id': '-staff__steam_id'}
        allowed_fields = ['staff__name', '-staff__name', 'rank_priority', '-rank_priority', 
                         'staff__steam_id', '-staff__steam_id', 'timezone', '-timezone', 
                         'is_active', '-is_active', 'rank', '-rank',
                         'name', '-name', 'steam_id', '-steam_id']  # Include original names for mapping
        valid_order_fields = []
        for field in order_fields:
            if field in allowed_fields:
                # Map to correct field name if needed
                valid_order_fields.append(field_mapping.get(field, field))
        
        if valid_order_fields:
            return queryset.order_by(*valid_order_fields)
        
        # Default ordering
        return queryset.order_by('rank_priority', 'staff__name')


class StaffRosterDetailView(generics.RetrieveAPIView):
    """Get a specific staff member."""
    serializer_class = StaffRosterSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = StaffRoster.objects.all()  # Include inactive/legacy staff


class StaffSyncView(APIView):
    """Trigger staff roster sync from Google Sheets."""
    permission_classes = [permissions.IsAuthenticated, IsManager]

    def post(self, request):
        try:
            service = StaffSyncService()
            log = service.sync_staff_roster()
            return Response({
                'message': 'Sync completed successfully',
                'details': StaffSyncLogSerializer(log).data
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get(self, request):
        """Get current sync configuration."""
        try:
            service = StaffSyncService()
            return Response({
                'google_sheets_id': service.sheet_id,
                'sheet_name': service.SHEET_NAME,
                'sheet_url': service.sheet_url,
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class StaffSyncLogListView(generics.ListAPIView):
    """List sync log entries."""
    serializer_class = StaffSyncLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsManager]
    queryset = StaffSyncLog.objects.all()[:20]


class SteamNameSyncView(APIView):
    """Trigger Steam name sync for all staff members. SYSADMIN only."""
    permission_classes = [permissions.IsAuthenticated, IsSysAdmin]

    def post(self, request):
        """Trigger an immediate Steam name sync."""
        from .tasks import sync_staff_steam_names
        
        try:
            # Run the task synchronously for immediate feedback
            result = sync_staff_steam_names()
            
            return Response({
                'message': 'Steam name sync completed',
                'success': result.get('success', False),
                'updated': result.get('updated', 0),
                'total': result.get('total', 0),
                'errors': result.get('errors'),
            })
        except Exception as e:
            return Response({
                'error': str(e),
                'success': False,
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get(self, request):
        """Get Steam name sync status for staff members."""
        from django.db.models import Count, Q

        from .models import Staff

        # Get counts
        total_staff = Staff.objects.filter(staff_status='active').count()
        with_steam_name = Staff.objects.filter(
            staff_status='active',
            steam_name__isnull=False
        ).exclude(steam_name='').count()
        
        # Get recently synced
        recently_synced = Staff.objects.filter(
            staff_status='active',
            steam_name_last_updated__isnull=False
        ).order_by('-steam_name_last_updated')[:5]
        
        return Response({
            'total_staff': total_staff,
            'with_steam_name': with_steam_name,
            'without_steam_name': total_staff - with_steam_name,
            'recently_synced': [
                {
                    'name': s.name,
                    'steam_name': s.steam_name,
                    'last_updated': s.steam_name_last_updated.isoformat() if s.steam_name_last_updated else None,
                }
                for s in recently_synced
            ],
        })


class RolePrioritiesView(APIView):
    """Get all role priorities and colors."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        roles = []
        for role, priority in settings.STAFF_ROLE_PRIORITIES.items():
            roles.append({
                'role': role,
                'priority': priority,
                'color': settings.STAFF_ROLE_COLORS.get(role, '#808080')
            })
        
        # Sort by priority
        roles.sort(key=lambda x: x['priority'])
        return Response(roles)


class MyStaffProfileView(APIView):
    """Get current user's staff profile."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Try to find roster entry
        roster = StaffRoster.objects.filter(
            is_active=True
        ).filter(
            steam_id=user.steam_id
        ).first() if user.steam_id else None
        
        if not roster and user.discord_id:
            roster = StaffRoster.objects.filter(
                is_active=True,
                discord_id=user.discord_id
            ).first()
        
        if roster:
            return Response(StaffRosterSerializer(roster).data)
        
        return Response(
            {'message': 'No staff profile found'},
            status=status.HTTP_404_NOT_FOUND
        )


class DiscordStatusSyncView(APIView):
    """Manually trigger Discord status sync."""
    permission_classes = [permissions.IsAuthenticated, IsManager]

    def post(self, request):
        try:
            # Check if Discord bot is configured
            if not settings.DISCORD_BOT_TOKEN or not settings.DISCORD_GUILD_ID:
                return Response(
                    {'error': 'Discord bot is not configured', 'configured': False},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            bot = get_bot_instance()
            if not bot.is_running:
                return Response(
                    {'error': 'Discord bot is not running', 'configured': True},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            # Run async sync
            asyncio.run(sync_discord_statuses())
            
            return Response({
                'message': 'Discord status sync completed successfully'
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DiscordBotStatusView(APIView):
    """Get Discord bot status."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Check if Discord bot is configured
        configured = bool(settings.DISCORD_BOT_TOKEN and settings.DISCORD_GUILD_ID)
        
        if not configured:
            return Response({
                'configured': False,
                'is_running': False,
                'guild_id': None,
                'message': 'Discord bot is not configured. Using in-app activity tracking.'
            })
        
        bot = get_bot_instance()
        return Response({
            'configured': True,
            'is_running': bot.is_running,
            'guild_id': bot.guild_id,
        })


class StaffDetailsView(generics.RetrieveAPIView):
    """Get comprehensive staff member details including time tracking."""
    serializer_class = StaffDetailsSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaffManager]
    queryset = StaffRoster.objects.all()  # Include inactive/legacy staff


class StaffSessionsView(generics.ListAPIView):
    """Get server sessions for a specific staff member."""
    serializer_class = ServerSessionSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaffManager]
    
    def get_queryset(self):
        staff_id = self.kwargs.get('pk')
        queryset = ServerSession.objects.filter(staff_id=staff_id)
        
        # Filter by server if provided
        server_id = self.request.query_params.get('server')
        if server_id:
            queryset = queryset.filter(server_id=server_id)
        
        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(join_time__gte=start_date)
        if end_date:
            queryset = queryset.filter(join_time__lte=end_date)
        
        # Filter active sessions only
        active_only = self.request.query_params.get('active_only')
        if active_only == 'true':
            queryset = queryset.filter(leave_time__isnull=True)
        
        return queryset.order_by('-join_time')


class StaffStatsView(APIView):
    """Get aggregated statistics for a specific staff member."""
    permission_classes = [permissions.IsAuthenticated, IsStaffManager]
    
    def get(self, request, pk):
        try:
            staff = StaffRoster.objects.get(pk=pk, is_active=True)
        except StaffRoster.DoesNotExist:
            return Response(
                {'error': 'Staff member not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        period_type = request.query_params.get('period', 'weekly')
        server_id = request.query_params.get('server')
        
        # Build query
        queryset = ServerSessionAggregate.objects.filter(
            staff=staff,
            period_type=period_type
        )
        
        if server_id:
            queryset = queryset.filter(server_id=server_id)
        
        # Get aggregates
        aggregates = queryset.order_by('-period_start')[:30]
        
        return Response({
            'staff_id': staff.id,
            'staff_name': staff.name,
            'period_type': period_type,
            'aggregates': ServerSessionAggregateSerializer(aggregates, many=True).data
        })


class BackfillLastSeenView(APIView):
    """Backfill last_seen timestamps for staff members based on server sessions."""
    permission_classes = [permissions.IsAuthenticated, IsManager]
    
    def get(self, request):
        """
        Get information about the backfill status.
        Shows how many staff members need backfilling.
        """
        from django.utils import timezone

        # Count staff members that need backfilling
        all_staff = Staff.objects.all()
        needs_update = 0
        already_updated = 0
        no_sessions = 0
        
        for staff in all_staff:
            most_recent_session = ServerSession.objects.filter(
                staff=staff,
                leave_time__isnull=False
            ).order_by('-leave_time').first()
            
            if most_recent_session:
                if staff.last_seen is None or staff.last_seen < most_recent_session.leave_time:
                    needs_update += 1
                else:
                    already_updated += 1
            else:
                no_sessions += 1
        
        return Response({
            'total_staff': all_staff.count(),
            'needs_update': needs_update,
            'already_updated': already_updated,
            'no_sessions': no_sessions,
            'message': f'{needs_update} staff members need backfilling',
            'endpoint': '/api/staff/backfill-last-seen/',
            'method': 'POST',
            'description': 'POST to this endpoint to backfill last_seen timestamps for all staff members'
        })
    
    def post(self, request):
        """
        Backfill last_seen timestamps for all staff members.
        This updates Staff.last_seen based on their most recent ServerSession.leave_time.
        """
        from django.utils import timezone

        # Get all staff members
        all_staff = Staff.objects.all()
        updated_count = 0
        skipped_count = 0
        errors = []
        
        for staff in all_staff:
            try:
                # Find their most recent session with a leave time
                most_recent_session = ServerSession.objects.filter(
                    staff=staff,
                    leave_time__isnull=False
                ).order_by('-leave_time').first()
                
                if most_recent_session:
                    # Update last_seen if it's None or older than the session leave_time
                    if staff.last_seen is None or staff.last_seen < most_recent_session.leave_time:
                        staff.last_seen = most_recent_session.leave_time
                        staff.save(update_fields=['last_seen'])
                        updated_count += 1
                    else:
                        skipped_count += 1
                else:
                    skipped_count += 1
            except Exception as e:
                errors.append(f"Error updating {staff.name}: {str(e)}")
                skipped_count += 1
        
        return Response({
            'success': True,
            'updated': updated_count,
            'skipped': skipped_count,
            'total': all_staff.count(),
            'errors': errors,
            'message': f'Successfully updated {updated_count} staff members'
        }, status=status.HTTP_200_OK)


class FixLastSeenView(APIView):
    """Fix last_seen timestamps - reset to correct values or None for staff without sessions."""
    permission_classes = [permissions.IsAuthenticated, IsManager]
    
    def get(self, request):
        """
        Get detailed information about last_seen values for all staff.
        Shows which staff have incorrect last_seen values.
        """
        from django.utils import timezone
        
        results = []
        needs_fix = 0
        correct = 0
        
        all_staff = Staff.objects.all().order_by('name')
        
        for staff in all_staff:
            # Get most recent completed session
            most_recent_session = ServerSession.objects.filter(
                staff=staff,
                leave_time__isnull=False
            ).order_by('-leave_time').first()
            
            session_count = ServerSession.objects.filter(staff=staff).count()
            
            if most_recent_session:
                # Staff has sessions - last_seen should match most recent session leave_time
                correct_last_seen = most_recent_session.leave_time
                is_correct = staff.last_seen == correct_last_seen
            else:
                # Staff has no sessions - last_seen should be None
                correct_last_seen = None
                is_correct = staff.last_seen is None
            
            if not is_correct:
                needs_fix += 1
            else:
                correct += 1
            
            results.append({
                'name': staff.name,
                'steam_id': staff.steam_id,
                'session_count': session_count,
                'current_last_seen': staff.last_seen.isoformat() if staff.last_seen else None,
                'correct_last_seen': correct_last_seen.isoformat() if correct_last_seen else None,
                'is_correct': is_correct,
                'needs_fix': not is_correct
            })
        
        # Sort by needs_fix first
        results.sort(key=lambda x: (not x['needs_fix'], x['name']))
        
        return Response({
            'total_staff': all_staff.count(),
            'needs_fix': needs_fix,
            'correct': correct,
            'staff': results,
            'endpoint': '/api/staff/fix-last-seen/',
            'method': 'POST to fix all incorrect last_seen values'
        })
    
    def post(self, request):
        """
        Fix all last_seen timestamps:
        - Staff WITH sessions: Set last_seen to most recent session leave_time
        - Staff WITHOUT sessions: Set last_seen to None (will show "Never")
        """
        from django.utils import timezone
        
        all_staff = Staff.objects.all()
        fixed_with_session = 0
        fixed_without_session = 0
        already_correct = 0
        errors = []
        
        for staff in all_staff:
            try:
                # Get most recent completed session
                most_recent_session = ServerSession.objects.filter(
                    staff=staff,
                    leave_time__isnull=False
                ).order_by('-leave_time').first()
                
                if most_recent_session:
                    # Staff has sessions - set last_seen to most recent session
                    if staff.last_seen != most_recent_session.leave_time:
                        staff.last_seen = most_recent_session.leave_time
                        staff.save(update_fields=['last_seen'])
                        fixed_with_session += 1
                    else:
                        already_correct += 1
                else:
                    # Staff has NO sessions - reset last_seen to None
                    if staff.last_seen is not None:
                        staff.last_seen = None
                        staff.save(update_fields=['last_seen'])
                        fixed_without_session += 1
                    else:
                        already_correct += 1
                        
            except Exception as e:
                errors.append(f"Error fixing {staff.name}: {str(e)}")
        
        return Response({
            'success': True,
            'fixed_with_session': fixed_with_session,
            'fixed_without_session': fixed_without_session,
            'already_correct': already_correct,
            'total': all_staff.count(),
            'errors': errors,
            'message': f'Fixed {fixed_with_session + fixed_without_session} staff members ({fixed_with_session} with sessions, {fixed_without_session} without sessions set to Never)'
        }, status=status.HTTP_200_OK)


class ServerTimeLeaderboardView(APIView):
    """Get leaderboard for server time (weekly/monthly)."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        from datetime import timedelta

        from django.db.models import Sum
        from django.utils import timezone

        period = request.query_params.get('period', 'weekly')  # 'weekly' or 'monthly'
        offset = int(request.query_params.get('offset', 0))  # 0 = current, 1 = previous, etc.
        
        now = timezone.now()
        
        if period == 'weekly':
            # Calculate week start (Saturday is reset day)
            week_start = get_week_start(now)
            week_start = week_start if isinstance(week_start, timezone.datetime) else timezone.datetime.combine(week_start, timezone.datetime.min.time(), tzinfo=now.tzinfo)
            
            # Apply offset
            week_start = week_start - timedelta(weeks=offset)
            week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
            
            period_start = week_start
            period_end = week_end
            period_label = f"Week of {week_start.strftime('%b %d, %Y')}"
            
        else:  # monthly
            # Calculate month start
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            # Apply offset
            for _ in range(offset):
                month_start = (month_start - timedelta(days=1)).replace(day=1)
            
            # Calculate month end
            next_month = month_start.replace(day=28) + timedelta(days=4)
            month_end = next_month.replace(day=1) - timedelta(seconds=1)
            
            period_start = month_start
            period_end = month_end
            period_label = month_start.strftime('%B %Y')
        
        # Query sessions within the period
        sessions = ServerSession.objects.filter(
            join_time__gte=period_start,
            join_time__lte=period_end,
            leave_time__isnull=False  # Only completed sessions
        ).select_related('staff')
        
        # Aggregate by staff
        staff_times = {}
        for session in sessions:
            staff_id = session.staff_id
            if staff_id not in staff_times:
                staff_times[staff_id] = {
                    'staff': session.staff,
                    'total_seconds': 0,
                    'session_count': 0,
                }
            staff_times[staff_id]['total_seconds'] += session.duration
            staff_times[staff_id]['session_count'] += 1
        
        # Get roster info for active staff (excluding builders if setting enabled)
        from apps.system_settings.models import SystemSetting
        roster_queryset = StaffRoster.objects.filter(is_active=True).select_related('staff')
        
        if SystemSetting.exclude_builders():
            from django.db.models import Q
            roster_queryset = roster_queryset.exclude(Q(rank__icontains='builder'))
        
        roster_map = {}
        for roster in roster_queryset:
            roster_map[roster.staff_id] = roster
        
        # Build leaderboard
        leaderboard = []
        for staff_id, data in staff_times.items():
            roster = roster_map.get(staff_id)
            if not roster:
                continue  # Skip non-active staff
                
            total_seconds = data['total_seconds']
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            
            leaderboard.append({
                'staff_id': roster.id,  # Use roster ID for navigation, not steam_id
                'steam_id': staff_id,
                'name': data['staff'].name,
                'role': roster.rank,
                'role_color': settings.STAFF_ROLE_COLORS.get(roster.rank, '#808080'),
                'role_priority': roster.rank_priority,
                'total_seconds': total_seconds,
                'total_time_formatted': f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m",
                'session_count': data['session_count'],
                'avg_session_seconds': total_seconds // data['session_count'] if data['session_count'] > 0 else 0,
            })
        
        # Sort by total time (descending)
        leaderboard.sort(key=lambda x: x['total_seconds'], reverse=True)
        
        # Add ranks
        for i, entry in enumerate(leaderboard):
            entry['rank'] = i + 1
        
        return Response({
            'period': period,
            'period_label': period_label,
            'period_start': period_start.isoformat(),
            'period_end': period_end.isoformat(),
            'offset': offset,
            'leaderboard': leaderboard,
        })


class StaffDailyBreakdownView(APIView):
    """Get daily server time breakdown for a staff member (Mon-Sun)."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, pk):
        from datetime import timedelta

        from django.utils import timezone

        week_offset = int(request.query_params.get('week_offset', 0))  # 0 = current, 1 = last week
        
        now = timezone.now()
        
        # Calculate week start (Saturday is reset day) for current week
        current_week_start = get_week_start(now)
        current_week_start = current_week_start if isinstance(current_week_start, timezone.datetime) else timezone.datetime.combine(current_week_start, timezone.datetime.min.time(), tzinfo=now.tzinfo)
        
        # Calculate the requested week
        requested_week_start = current_week_start - timedelta(weeks=week_offset)
        requested_week_end = requested_week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
        
        # Calculate previous week for comparison
        previous_week_start = requested_week_start - timedelta(weeks=1)
        previous_week_end = previous_week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
        
        # Get staff member
        try:
            staff = Staff.objects.get(steam_id=pk)
        except Staff.DoesNotExist:
            # Try by roster ID
            try:
                roster = StaffRoster.objects.get(pk=pk)
                staff = roster.staff
            except StaffRoster.DoesNotExist:
                return Response({'error': 'Staff not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get sessions for current and previous week
        current_sessions = ServerSession.objects.filter(
            staff=staff,
            join_time__gte=requested_week_start,
            join_time__lte=requested_week_end,
            leave_time__isnull=False
        )
        
        previous_sessions = ServerSession.objects.filter(
            staff=staff,
            join_time__gte=previous_week_start,
            join_time__lte=previous_week_end,
            leave_time__isnull=False
        )
        
        # Initialize daily breakdown
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        current_breakdown = {i: 0 for i in range(7)}  # 0=Mon, 6=Sun
        previous_breakdown = {i: 0 for i in range(7)}
        
        # Aggregate current week sessions by day
        for session in current_sessions:
            day_of_week = session.join_time.weekday()
            current_breakdown[day_of_week] += session.duration
        
        # Aggregate previous week sessions by day
        for session in previous_sessions:
            day_of_week = session.join_time.weekday()
            previous_breakdown[day_of_week] += session.duration
        
        # Find max day
        max_seconds = max(current_breakdown.values()) if current_breakdown else 0
        max_day = None
        if max_seconds > 0:
            for day_num, seconds in current_breakdown.items():
                if seconds == max_seconds:
                    max_day = day_num
                    break
        
        # Format results
        daily_data = []
        total_current = 0
        total_previous = 0
        
        for day_num in range(7):
            current_secs = current_breakdown[day_num]
            previous_secs = previous_breakdown[day_num]
            
            total_current += current_secs
            total_previous += previous_secs
            
            # Format time
            current_hours = current_secs // 3600
            current_mins = (current_secs % 3600) // 60
            previous_hours = previous_secs // 3600
            previous_mins = (previous_secs % 3600) // 60
            
            daily_data.append({
                'day': days[day_num],
                'day_short': days[day_num][:3],
                'day_number': day_num,
                'current_seconds': current_secs,
                'current_formatted': f"{current_hours}h {current_mins}m" if current_hours > 0 else f"{current_mins}m",
                'previous_seconds': previous_secs,
                'previous_formatted': f"{previous_hours}h {previous_mins}m" if previous_hours > 0 else f"{previous_mins}m",
                'is_max': day_num == max_day,
            })
        
        # Format totals
        total_current_hours = total_current // 3600
        total_current_mins = (total_current % 3600) // 60
        total_previous_hours = total_previous // 3600
        total_previous_mins = (total_previous % 3600) // 60
        
        return Response({
            'staff_id': staff.steam_id,
            'staff_name': staff.name,
            'week_offset': week_offset,
            'week_start': requested_week_start.isoformat(),
            'week_end': requested_week_end.isoformat(),
            'week_label': f"Week of {requested_week_start.strftime('%b %d')}",
            'previous_week_label': f"Week of {previous_week_start.strftime('%b %d')}",
            'daily_breakdown': daily_data,
            'total_current_seconds': total_current,
            'total_current_formatted': f"{total_current_hours}h {total_current_mins}m" if total_current_hours > 0 else f"{total_current_mins}m",
            'total_previous_seconds': total_previous,
            'total_previous_formatted': f"{total_previous_hours}h {total_previous_mins}m" if total_previous_hours > 0 else f"{total_previous_mins}m",
            'max_day': days[max_day] if max_day is not None else None,
        })


class RecentPromotionsView(APIView):
    """
    Get recent staff role changes grouped by week.
    Shows promotions, demotions, joins, removals, etc.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from collections import defaultdict
        from datetime import timedelta

        from apps.system_settings.models import SystemSetting
        from django.db.models import Q

        from .models import StaffHistoryEvent
        from .serializers import StaffHistoryEventSerializer

        # Get week offset from query params (0 = current week, 1 = last week, etc.)
        week_offset = int(request.query_params.get('offset', 0))
        
        # Calculate week boundaries (Monday-Sunday)
        today = timezone.now().date()
        current_week_start = today - timedelta(days=today.weekday())  # Monday
        
        # Apply offset
        requested_week_start = current_week_start - timedelta(weeks=week_offset)
        requested_week_end = requested_week_start + timedelta(days=6)  # Sunday
        
        # Convert to datetime for filtering
        week_start_dt = timezone.make_aware(
            timezone.datetime.combine(requested_week_start, timezone.datetime.min.time())
        )
        week_end_dt = timezone.make_aware(
            timezone.datetime.combine(requested_week_end, timezone.datetime.max.time())
        )
        
        # Get all events for this week
        events = StaffHistoryEvent.objects.filter(
            event_date__gte=week_start_dt,
            event_date__lte=week_end_dt
        ).select_related('staff', 'created_by').order_by('-event_date')
        
        # Exclude builder-related events if system setting is enabled
        if SystemSetting.exclude_builders():
            events = events.exclude(
                Q(old_rank__icontains='builder') | 
                Q(new_rank__icontains='builder')
            )
        
        # Categorize events by type
        categorized = {
            'promotions': [],
            'demotions': [],
            'joins': [],
            'removals': [],
            'rejoined': [],
            'role_changes': [],
        }
        
        for event in events:
            serialized = StaffHistoryEventSerializer(event).data
            
            if event.event_type == 'promoted':
                categorized['promotions'].append(serialized)
            elif event.event_type == 'demoted':
                categorized['demotions'].append(serialized)
            elif event.event_type == 'joined':
                categorized['joins'].append(serialized)
            elif event.event_type in ['removed', 'left']:
                categorized['removals'].append(serialized)
            elif event.event_type == 'rejoined':
                categorized['rejoined'].append(serialized)
            elif event.event_type == 'role_change':
                # Classify based on priority change
                if event.is_promotion:
                    categorized['promotions'].append(serialized)
                elif event.is_demotion:
                    categorized['demotions'].append(serialized)
                else:
                    categorized['role_changes'].append(serialized)
        
        # Summary stats
        total_events = events.count()
        
        return Response({
            'week_offset': week_offset,
            'week_start': requested_week_start.isoformat(),
            'week_end': requested_week_end.isoformat(),
            'week_label': f"Week of {requested_week_start.strftime('%b %d, %Y')}",
            'total_events': total_events,
            'summary': {
                'promotions': len(categorized['promotions']),
                'demotions': len(categorized['demotions']),
                'joins': len(categorized['joins']),
                'removals': len(categorized['removals']),
                'rejoined': len(categorized['rejoined']),
                'role_changes': len(categorized['role_changes']),
            },
            'events': categorized,
            'all_events': StaffHistoryEventSerializer(events, many=True).data,
        })


class DeleteHistoryEventView(APIView):
    """
    Delete a staff history event. SYSADMIN only.
    """
    permission_classes = [permissions.IsAuthenticated, IsSysAdmin]

    def delete(self, request, event_id):
        from .models import StaffHistoryEvent
        
        try:
            event = StaffHistoryEvent.objects.get(id=event_id)
            staff_name = event.staff.name
            event_type = event.get_event_type_display()
            event.delete()
            
            return Response({
                'message': f'Deleted {event_type} event for {staff_name}',
                'deleted_id': event_id,
            })
        except StaffHistoryEvent.DoesNotExist:
            return Response(
                {'error': 'History event not found'},
                status=status.HTTP_404_NOT_FOUND
            )
