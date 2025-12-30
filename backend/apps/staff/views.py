from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings

from .models import StaffRoster, StaffSyncLog
from .serializers import (
    StaffRosterSerializer,
    StaffSyncLogSerializer,
    RolePrioritySerializer,
)
from .services import StaffSyncService
from apps.accounts.permissions import IsManager


class StaffRosterListView(generics.ListAPIView):
    """List all staff members from roster."""
    serializer_class = StaffRosterSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = StaffRoster.objects.filter(is_active=True)
        
        # Filter by rank if provided
        rank = self.request.query_params.get('rank')
        if rank:
            queryset = queryset.filter(rank=rank)
        
        return queryset.order_by('rank', 'name')


class StaffRosterDetailView(generics.RetrieveAPIView):
    """Get a specific staff member."""
    serializer_class = StaffRosterSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = StaffRoster.objects.filter(is_active=True)


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
