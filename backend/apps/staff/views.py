import asyncio

from apps.accounts.permissions import IsManager, IsStaffManager
from django.conf import settings
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
        # By default, show only active staff
        # Allow showing inactive/legacy staff with ?show_inactive=true
        show_inactive = self.request.query_params.get('show_inactive', 'false').lower() == 'true'
        
        if show_inactive:
            # Show all staff including inactive
            queryset = StaffRoster.objects.all()
        else:
            # Default: only active staff
            queryset = StaffRoster.objects.filter(is_active=True)
        
        # Filter by rank if provided
        rank = self.request.query_params.get('rank')
        if rank:
            queryset = queryset.filter(rank=rank)
        
        # Search by name or Steam ID
        search = self.request.query_params.get('search')
        if search:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(username__icontains=search) |
                Q(steam_id__icontains=search)
            )
        
        # Filter by role
        role = self.request.query_params.get('role')
        if role and role != 'all':
            queryset = queryset.filter(rank=role)
        
        # Handle ordering parameter
        ordering = self.request.query_params.get('ordering', 'rank_priority,name')
        # Allow multiple ordering fields separated by comma
        order_fields = [field.strip() for field in ordering.split(',')]
        # Validate ordering fields to prevent SQL injection
        allowed_fields = ['name', '-name', 'rank_priority', '-rank_priority', 
                         'steam_id', '-steam_id', 'timezone', '-timezone', 
                         'is_active', '-is_active', 'rank', '-rank']
        valid_order_fields = [field for field in order_fields if field in allowed_fields]
        
        if valid_order_fields:
            return queryset.order_by(*valid_order_fields)
        
        # Default ordering
        return queryset.order_by('rank_priority', 'name')


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
