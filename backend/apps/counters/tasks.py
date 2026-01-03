"""
Celery tasks for counter management.
"""
import logging
from datetime import timedelta

from apps.utils import get_week_start
from celery import shared_task
from django.utils import timezone

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
def check_weekly_reset():
    """
    Check and perform weekly counter resets on Saturday.
    
    This task runs every Saturday at midnight to:
    1. Create weekly snapshots of sit/ticket counts
    2. Archive the previous week's statistics
    
    The week runs Saturday-Friday, with Saturday being the reset day.
    """
    from .models import Counter, CounterHistory, CounterSnapshot
    
    today = timezone.now().date()
    
    # Only run on Saturday (weekday 5)
    if today.weekday() != 5:
        logger.info(f"Weekly reset skipped - not Saturday (today is weekday {today.weekday()})")
        return
    
    # Calculate the week that just ended (last Saturday to yesterday/Friday)
    last_week_start = get_week_start(today - timedelta(days=1))  # Get previous week's Saturday
    last_week_end = last_week_start + timedelta(days=6)  # Friday
    
    logger.info(f"Weekly reset running for week: {last_week_start} to {last_week_end}")
    
    # Get all total counters to identify users
    counters = Counter.objects.filter(period_type='total')
    
    users_processed = set()
    weekly_snapshots_created = 0
    
    for counter in counters:
        if counter.user_id in users_processed:
            continue
        
        # Calculate weekly totals from history
        weekly_history = CounterHistory.objects.filter(
            user=counter.user,
            timestamp__date__gte=last_week_start,
            timestamp__date__lte=last_week_end,
            action__in=['increment', 'decrement']
        )
        
        weekly_sits = 0
        for entry in weekly_history.filter(counter_type='sit'):
            weekly_sits += (entry.new_value - entry.old_value)
        
        weekly_tickets = 0
        for entry in weekly_history.filter(counter_type='ticket'):
            weekly_tickets += (entry.new_value - entry.old_value)
        
        # Create weekly snapshot (using last day of week as the date)
        if weekly_sits > 0 or weekly_tickets > 0:
            CounterSnapshot.objects.update_or_create(
                user=counter.user,
                date=last_week_end,
                defaults={
                    'sit_count': weekly_sits,
                    'ticket_count': weekly_tickets,
                }
            )
            weekly_snapshots_created += 1
        
        users_processed.add(counter.user_id)
    
    logger.info(
        f"Weekly reset completed: {len(users_processed)} users processed, "
        f"{weekly_snapshots_created} weekly snapshots created"
    )


@shared_task
def calculate_weekly_stats():
    """Calculate weekly statistics for leaderboard."""
    from django.db.models import Sum

    from .models import Counter, CounterHistory
    
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
