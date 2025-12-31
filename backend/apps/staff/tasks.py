"""
Celery tasks for staff roster management.
"""
import asyncio
import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def sync_staff_roster():
    """Sync staff roster from Google Sheets."""
    from .services import StaffSyncService
    
    try:
        service = StaffSyncService()
        log = service.sync_staff_roster()
        
        # Return JSON-serializable dict instead of model instance
        result = {
            'success': log.success,
            'records_synced': log.records_synced,
            'records_added': log.records_added,
            'records_updated': log.records_updated,
            'records_removed': log.records_removed,
            'error_message': log.error_message,
            'synced_at': log.synced_at.isoformat() if log.synced_at else None,
        }
        
        logger.info(f"Staff roster sync completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error syncing staff roster: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def sync_discord_statuses_task():
    """Sync Discord statuses for all staff members."""
    from django.conf import settings

    from .discord_service import get_bot_instance, sync_discord_statuses

    # Check if Discord bot is configured
    if not getattr(settings, 'DISCORD_BOT_TOKEN', None) or not getattr(settings, 'DISCORD_GUILD_ID', None):
        logger.info("Discord bot not configured, skipping status sync")
        return {'success': False, 'error': 'Bot not configured'}
    
    try:
        bot = get_bot_instance()
        if not bot.is_running:
            logger.warning("Discord bot is not running, skipping status sync")
            return {'success': False, 'error': 'Bot not running'}
        
        # Run async function
        asyncio.run(sync_discord_statuses())
        
        logger.info("Discord status sync completed")
        return {'success': True}
        
    except Exception as e:
        logger.error(f"Error syncing Discord statuses: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def mark_inactive_staff():
    """Mark staff as inactive if not seen in last 5 minutes."""
    from datetime import timedelta

    from django.utils import timezone

    from .models import StaffRoster
    
    try:
        threshold = timezone.now() - timedelta(minutes=5)
        
        # Mark staff as inactive if last_seen is older than threshold
        updated = StaffRoster.objects.filter(
            is_active_in_app=True,
            last_seen__lt=threshold
        ).update(is_active_in_app=False)
        
        logger.info(f"Marked {updated} staff members as inactive")
        return {'success': True, 'marked_inactive': updated}
        
    except Exception as e:
        logger.error(f"Error marking inactive staff: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def update_user_from_roster(user_id: int):
    """Update a single user's information from roster."""
    from django.conf import settings
    from django.contrib.auth import get_user_model

    from .models import StaffRoster
    
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


@shared_task
def aggregate_server_sessions():
    """Aggregate server sessions for statistics."""
    from datetime import date, timedelta
    from django.db.models import Sum, Count, Avg
    from .models import StaffRoster, ServerSession, ServerSessionAggregate
    from apps.servers.models import GameServer
    
    try:
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        # Get all active staff
        staff_members = StaffRoster.objects.filter(is_active=True)
        servers = GameServer.objects.filter(is_active=True)
        
        aggregated_count = 0
        
        for staff in staff_members:
            # Daily aggregation for yesterday
            for server in servers:
                sessions = ServerSession.objects.filter(
                    staff=staff,
                    server=server,
                    join_time__date=yesterday,
                    leave_time__isnull=False
                )
                
                if sessions.exists():
                    stats = sessions.aggregate(
                        total_time=Sum('duration'),
                        session_count=Count('id'),
                        avg_duration=Avg('duration'),
                        longest_session=Sum('duration')  # This should be Max but simplified for now
                    )
                    
                    aggregate, created = ServerSessionAggregate.objects.update_or_create(
                        staff=staff,
                        server=server,
                        period_type='daily',
                        period_start=yesterday,
                        defaults={
                            'period_end': yesterday,
                            'total_time': stats['total_time'] or 0,
                            'session_count': stats['session_count'] or 0,
                            'avg_session_time': int(stats['avg_duration'] or 0),
                            'longest_session': stats['longest_session'] or 0,
                        }
                    )
                    aggregated_count += 1
            
            # Weekly aggregation
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            
            for server in servers:
                sessions = ServerSession.objects.filter(
                    staff=staff,
                    server=server,
                    join_time__date__gte=week_start,
                    join_time__date__lte=week_end,
                    leave_time__isnull=False
                )
                
                if sessions.exists():
                    stats = sessions.aggregate(
                        total_time=Sum('duration'),
                        session_count=Count('id'),
                        avg_duration=Avg('duration'),
                        longest_session=Sum('duration')
                    )
                    
                    ServerSessionAggregate.objects.update_or_create(
                        staff=staff,
                        server=server,
                        period_type='weekly',
                        period_start=week_start,
                        defaults={
                            'period_end': week_end,
                            'total_time': stats['total_time'] or 0,
                            'session_count': stats['session_count'] or 0,
                            'avg_session_time': int(stats['avg_duration'] or 0),
                            'longest_session': stats['longest_session'] or 0,
                        }
                    )
            
            # Monthly aggregation
            month_start = today.replace(day=1)
            
            for server in servers:
                sessions = ServerSession.objects.filter(
                    staff=staff,
                    server=server,
                    join_time__date__gte=month_start,
                    join_time__date__lte=today,
                    leave_time__isnull=False
                )
                
                if sessions.exists():
                    stats = sessions.aggregate(
                        total_time=Sum('duration'),
                        session_count=Count('id'),
                        avg_duration=Avg('duration'),
                        longest_session=Sum('duration')
                    )
                    
                    ServerSessionAggregate.objects.update_or_create(
                        staff=staff,
                        server=server,
                        period_type='monthly',
                        period_start=month_start,
                        defaults={
                            'total_time': stats['total_time'] or 0,
                            'session_count': stats['session_count'] or 0,
                            'avg_session_time': int(stats['avg_duration'] or 0),
                            'longest_session': stats['longest_session'] or 0,
                        }
                    )
        
        logger.info(f"Aggregated {aggregated_count} server sessions")
        return {'success': True, 'aggregated': aggregated_count}
        
    except Exception as e:
        logger.error(f"Error aggregating server sessions: {e}")
        return {'success': False, 'error': str(e)}
