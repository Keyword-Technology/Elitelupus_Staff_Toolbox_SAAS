"""
Celery tasks for server status monitoring.
"""
import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


def broadcast_server_status():
    """Broadcast current server status to all connected WebSocket clients."""
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer

    from .models import GameServer, ServerPlayer
    
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            logger.warning("No channel layer configured, skipping broadcast")
            return
            
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
        
        async_to_sync(channel_layer.group_send)(
            "server_status",
            {
                'type': 'status_update',
                'data': result
            }
        )
        logger.debug(f"Broadcasted server status to clients")
    except Exception as e:
        logger.error(f"Error broadcasting server status: {e}")


@shared_task
def refresh_all_servers():
    """Refresh status for all game servers."""
    from .models import GameServer
    from .services import ServerQueryService
    
    servers = GameServer.objects.filter(is_active=True)
    service = ServerQueryService()
    
    for server in servers:
        try:
            # The service.query_server handles all the updates internally
            status = service.query_server(server)
            logger.debug(f"Server {server.name}: {status}")
            
        except Exception as e:
            logger.error(f"Error refreshing server {server.name}: {e}")
    
    logger.info(f"Refreshed {servers.count()} servers")
    
    # Broadcast updated status to all WebSocket clients
    broadcast_server_status()


@shared_task
def refresh_single_server(server_id: int):
    """Refresh status for a single server."""
    from .models import GameServer
    from .services import ServerQueryService
    
    try:
        server = GameServer.objects.get(id=server_id)
        service = ServerQueryService()
        
        status = service.query_server(server)
        
        # Broadcast updated status to all WebSocket clients
        broadcast_server_status()
        
        return status.get('online', False)
        
    except GameServer.DoesNotExist:
        logger.error(f"Server {server_id} not found")
        return False
    except Exception as e:
        logger.error(f"Error refreshing server {server_id}: {e}")
        return False
