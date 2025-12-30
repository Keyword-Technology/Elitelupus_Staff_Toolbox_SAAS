"""
Celery tasks for staff roster management.
"""
from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task
def sync_staff_roster():
    """Sync staff roster from Google Sheets."""
    from .services import StaffSyncService
    
    try:
        service = StaffSyncService()
        result = service.sync_staff_roster()
        
        logger.info(f"Staff roster sync completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error syncing staff roster: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def update_user_from_roster(user_id: int):
    """Update a single user's information from roster."""
    from django.contrib.auth import get_user_model
    from .models import StaffRoster
    from django.conf import settings
    
    User = get_user_model()
    
    try:
        user = User.objects.get(id=user_id)
        
        # Try to find matching roster entry
        roster_entry = None
        
        if user.steam_id:
            roster_entry = StaffRoster.objects.filter(
                steam_id=user.steam_id,
                is_active=True
            ).first()
        
        if roster_entry:
            user.role = roster_entry.rank
            user.role_priority = settings.STAFF_ROLE_PRIORITIES.get(roster_entry.rank, 999)
            user.is_active_staff = True
            user.save(update_fields=['role', 'role_priority', 'is_active_staff'])
            
            logger.info(f"Updated user {user.username} from roster")
            return True
        
        return False
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return False
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        return False
