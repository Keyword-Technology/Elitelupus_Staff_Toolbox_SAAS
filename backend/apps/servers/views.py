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
        servers = GameServer.objects.filter(is_active=True)
        
        result = []
        for server in servers:
            staff_count = ServerPlayer.objects.filter(
                server=server, is_staff=True
            ).count()
            
            server_name = server.server_name or server.name
            map_name = server.map_name or 'Unknown'
            
            result.append({
                'id': server.id,
                'name': server.name,
                'server_name': server_name,
                'map_name': map_name,
                'current_players': server.current_players,
                'max_players': server.max_players,
                'is_online': server.is_online,
                'staff_online': staff_count,
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


class ServerHistoryView(generics.ListAPIView):
    """Get server status history."""
    serializer_class = ServerStatusLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        server_id = self.kwargs.get('pk')
        return ServerStatusLog.objects.filter(server_id=server_id)[:100]
