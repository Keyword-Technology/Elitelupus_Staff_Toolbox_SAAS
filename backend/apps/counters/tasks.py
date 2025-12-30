"""
Celery tasks for counter management.
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
def check_daily_reset():
    """Check and perform daily counter resets if needed."""
    from .models import Counter, CounterHistory, CounterSnapshot
    
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    
    # Get all total counters
    counters = Counter.objects.filter(period_type='total')
    
    users_processed = set()
    
    for counter in counters:
        if counter.user_id in users_processed:
            continue
        
        # Check if we already have today's snapshot
        existing = CounterSnapshot.objects.filter(
            user=counter.user,
            date=yesterday
        ).exists()
        
        if not existing:
            # Get user's daily counters
            sit_counter = Counter.objects.filter(
                user=counter.user,
                counter_type='sit',
                period_type='daily',
                period_start=yesterday
            ).first()
            
            ticket_counter = Counter.objects.filter(
                user=counter.user,
                counter_type='ticket',
                period_type='daily',
                period_start=yesterday
            ).first()
            
            # Create snapshot
            CounterSnapshot.objects.create(
                user=counter.user,
                date=yesterday,
                sit_count=sit_counter.count if sit_counter else 0,
                ticket_count=ticket_counter.count if ticket_counter else 0
            )
            
        users_processed.add(counter.user_id)
    
    logger.info(f"Daily counter check completed for {len(users_processed)} users")


@shared_task
def calculate_weekly_stats():
    """Calculate weekly statistics for leaderboard."""
    from .models import Counter, CounterHistory
    from django.db.models import Sum
    
    one_week_ago = timezone.now() - timedelta(days=7)
    
    # Get weekly totals for each user
    weekly_stats = CounterHistory.objects.filter(
        created_at__gte=one_week_ago,
        action='increment'
    ).values('user_id', 'counter_type').annotate(
        total=Sum('value')
    )
    
    logger.info(f"Calculated weekly stats for {len(weekly_stats)} entries")
    return list(weekly_stats)


@shared_task
def send_leaderboard_notification(user_id: int, position: int, counter_type: str):
    """Send notification when user reaches a new leaderboard position."""
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    try:
        user = User.objects.get(id=user_id)
        
        # Here you could integrate with Discord webhook or push notifications
        logger.info(
            f"Leaderboard notification: {user.username} reached #{position} "
            f"for {counter_type}"
        )
        
        return True
        
    except User.DoesNotExist:
        return False
