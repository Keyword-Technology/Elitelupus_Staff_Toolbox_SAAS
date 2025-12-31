import asyncio

from apps.accounts.permissions import IsManager
from django.conf import settings
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .discord_service import get_bot_instance, sync_discord_statuses
from .models import StaffRoster, StaffSyncLog
from .serializers import (RolePrioritySerializer, StaffRosterSerializer,
                          StaffSyncLogSerializer)
from .services import StaffSyncService


class StaffRosterListView(generics.ListAPIView):
    """List all staff members from roster."""
    serializer_class = StaffRosterSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Exclude Builder role and inactive staff
        queryset = StaffRoster.objects.filter(is_active=True).exclude(rank='Builder')
        
        # Filter by rank if provided
        rank = self.request.query_params.get('rank')
        if rank:
            queryset = queryset.filter(rank=rank)
        
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
    
    def get_paginate_by(self, queryset):
        """Allow dynamic page size from query parameter."""
        page_size = self.request.query_params.get('page_size')
        if page_size:
            try:
                return int(page_size)
            except ValueError:
                pass
        return 25  # Default page size


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
