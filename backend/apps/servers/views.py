from datetime import datetime, timedelta

from django.db.models import Avg, Count
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import GameServer, ServerPlayer, ServerStatusLog
from .serializers import (GameServerSerializer, ServerPlayerSerializer,
                          ServerStatusLogSerializer,
                          StaffDistributionSerializer)
from .services import ServerQueryService


class ServerListView(generics.ListAPIView):
    """List all game servers."""
    serializer_class = GameServerSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = GameServer.objects.filter(is_active=True)


class ServerDetailView(generics.RetrieveAPIView):
    """Get details of a specific server."""
    serializer_class = GameServerSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = GameServer.objects.all()


class ServerStatusView(APIView):
    """Get current status of all servers."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from django.conf import settings
        
        servers = GameServer.objects.filter(is_active=True)
        
        result = []
        for server in servers:
            staff_players = ServerPlayer.objects.filter(
                server=server, is_staff=True
            )
            
            server_name = server.server_name or server.name
            map_name = server.map_name or 'Unknown'
            
            # Build staff list with details including role color and priority
            staff_list = []
            for player in staff_players:
                rank = player.staff_rank or 'Unknown'
                staff_list.append({
                    'name': player.name,
                    'rank': rank,
                    'role_color': settings.STAFF_ROLE_COLORS.get(rank, '#999999'),
                    'role_priority': settings.STAFF_ROLE_PRIORITIES.get(rank, 999),
                    'steam_id': player.steam_id,
                })
            
            # Sort staff list by role priority (lower = higher rank)
            staff_list.sort(key=lambda x: x['role_priority'])
            
            result.append({
                'id': server.id,
                'name': server.name,
                'server_name': server_name,
                'map_name': map_name,
                'current_players': server.current_players,
                'max_players': server.max_players,
                'is_online': server.is_online,
                'staff_online': staff_players.count(),
                'staff_list': staff_list,
                'last_query': server.last_query,
            })
        
        return Response(result)


class RefreshServersView(APIView):
    """Refresh server status by querying servers."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        service = ServerQueryService()
        results = service.query_all_servers()
        
        return Response({
            'message': 'Servers refreshed',
            'results': results
        })


class ServerPlayersView(APIView):
    """Get players on a specific server."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            server = GameServer.objects.get(pk=pk)
            players = ServerPlayer.objects.filter(server=server)
            
            return Response({
                'server': GameServerSerializer(server).data,
                'players': ServerPlayerSerializer(players, many=True).data
            })
        except GameServer.DoesNotExist:
            return Response(
                {'error': 'Server not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class StaffDistributionView(APIView):
    """Get staff distribution across servers."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        service = ServerQueryService()
        distribution = service.get_staff_distribution()
        
        return Response(distribution)


class PlayerLookupView(APIView):
    """Look up a player by Steam ID or name across all servers."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from .services import normalize_name
        
        steam_id = request.query_params.get('steam_id')
        player_names = request.query_params.get('player_names', '').split(',')
        player_names = [name.strip() for name in player_names if name.strip()]
        
        if not steam_id and not player_names:
            return Response(
                {'error': 'steam_id or player_names parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Search for player across all servers
        # First try by Steam ID (for staff members)
        players = ServerPlayer.objects.none()
        if steam_id:
            players = ServerPlayer.objects.filter(steam_id__iexact=steam_id).select_related('server')
        
        # If not found by Steam ID, try by player names (with flexible matching)
        if not players.exists() and player_names:
            from django.db.models import Q

            # Build a query to match any of the player names (case-insensitive)
            name_query = Q()
            for name in player_names:
                # Exact match
                name_query |= Q(name__iexact=name)
                
                # Also try normalized version (without numbers)
                normalized = normalize_name(name)
                if normalized != name.lower():
                    # Find all players whose normalized name matches
                    all_players = ServerPlayer.objects.select_related('server')
                    for player in all_players:
                        if normalize_name(player.name) == normalized:
                            players = players | ServerPlayer.objects.filter(id=player.id)
            
            # Apply exact name matches
            if name_query:
                players = players | ServerPlayer.objects.filter(name_query).select_related('server')
        
        if not players.exists():
            return Response({
                'found': False,
                'message': 'Player not currently online on any server'
            })
        
        # Return all server instances where player is found
        player_data = []
        for player in players:
            player_data.append({
                'server': {
                    'id': player.server.id,
                    'name': player.server.name,
                },
                'player_name': player.name,
                'score': player.score,
                'duration': player.duration,
                'duration_formatted': player.duration_formatted,
                'is_staff': player.is_staff,
                'staff_rank': player.staff_rank,
                'last_seen': player.last_seen,
            })
        
        return Response({
            'found': True,
            'servers': player_data
        })


class ServerHistoryView(generics.ListAPIView):
    """Get server status history."""
    serializer_class = ServerStatusLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        server_id = self.kwargs.get('pk')
        return ServerStatusLog.objects.filter(server_id=server_id)[:100]


class ServerStatsView(APIView):
    """Get detailed server statistics including 24-hour staff tracking and daily averages."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            server = GameServer.objects.get(pk=pk)
        except GameServer.DoesNotExist:
            return Response(
                {'error': 'Server not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get logs from the last 24 hours
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        recent_logs = ServerStatusLog.objects.filter(
            server=server,
            timestamp__gte=last_24h
        ).order_by('timestamp')

        # Format 24-hour data
        hourly_data = []
        for log in recent_logs:
            hourly_data.append({
                'timestamp': log.timestamp.isoformat(),
                'staff_count': log.staff_count,
                'player_count': log.player_count,
                'is_online': log.is_online
            })

        # Get all historical data for daily averages (last 30 days)
        last_30d = now - timedelta(days=30)
        all_logs = ServerStatusLog.objects.filter(
            server=server,
            timestamp__gte=last_30d,
            is_online=True
        )

        # Calculate hourly averages across all days
        hourly_averages = []
        for hour in range(24):
            hour_logs = all_logs.filter(timestamp__hour=hour)
            if hour_logs.exists():
                avg_staff = hour_logs.aggregate(Avg('staff_count'))['staff_count__avg'] or 0
                avg_players = hour_logs.aggregate(Avg('player_count'))['player_count__avg'] or 0
                count = hour_logs.count()
            else:
                avg_staff = 0
                avg_players = 0
                count = 0
            
            hourly_averages.append({
                'hour': hour,
                'avg_staff': round(avg_staff, 2),
                'avg_players': round(avg_players, 2),
                'sample_count': count
            })

        # Get current server status
        current_staff = ServerPlayer.objects.filter(
            server=server,
            is_staff=True
        ).count()

        return Response({
            'server': GameServerSerializer(server).data,
            'current_staff': current_staff,
            'last_24h': hourly_data,
            'hourly_averages': hourly_averages,
            'stats_period': {
                'start': last_24h.isoformat(),
                'end': now.isoformat(),
                'average_period_days': 30
            }
        })
