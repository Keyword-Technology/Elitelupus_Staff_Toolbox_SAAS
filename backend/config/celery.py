"""
Celery configuration for Elitelupus Staff Toolbox SAAS.
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('elitelupus')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat Schedule
app.conf.beat_schedule = {
    # Refresh server status every minute
    'refresh-server-status-every-minute': {
        'task': 'apps.servers.tasks.refresh_all_servers',
        'schedule': 60.0,  # Every 60 seconds
    },
    # Sync staff roster every hour
    'sync-staff-roster-hourly': {
        'task': 'apps.staff.tasks.sync_staff_roster',
        'schedule': crontab(minute=0),  # Every hour at minute 0
    },
    # Daily leaderboard reset check
    'daily-leaderboard-check': {
        'task': 'apps.counters.tasks.check_daily_reset',
        'schedule': crontab(hour=0, minute=0),  # Every day at midnight
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
