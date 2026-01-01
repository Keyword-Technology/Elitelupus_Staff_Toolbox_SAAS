"""
Celery tasks for templates manager.
"""
import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def expire_steam_profile_notes():
    """
    Mark expired Steam profile notes as inactive.
    
    This task checks for notes where:
    - is_active is True
    - expires_at is set and in the past
    
    It then sets is_active=False and resolved_at to the current time.
    """
    from apps.templates_manager.models import SteamProfileNote
    
    now = timezone.now()
    
    # Find active notes that have expired
    expired_notes = SteamProfileNote.objects.filter(
        is_active=True,
        expires_at__isnull=False,
        expires_at__lt=now
    )
    
    count = expired_notes.count()
    
    if count > 0:
        # Update expired notes
        expired_notes.update(
            is_active=False,
            resolved_at=now
        )
        logger.info(f"Marked {count} expired Steam profile notes as inactive")
    else:
        logger.debug("No expired Steam profile notes found")
    
    return f"Processed {count} expired notes"
