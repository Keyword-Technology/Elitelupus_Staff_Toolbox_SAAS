"""
Celery tasks for server status monitoring.
"""
from celery import shared_task
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


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


@shared_task
def refresh_single_server(server_id: int):
    """Refresh status for a single server."""
    from .models import GameServer
    from .services import ServerQueryService
    
    try:
        server = GameServer.objects.get(id=server_id)
        service = ServerQueryService()
        
        status = service.query_server(server)
        return status.get('online', False)
        
    except GameServer.DoesNotExist:
        logger.error(f"Server {server_id} not found")
        return False
    except Exception as e:
        logger.error(f"Error refreshing server {server_id}: {e}")
        return False
