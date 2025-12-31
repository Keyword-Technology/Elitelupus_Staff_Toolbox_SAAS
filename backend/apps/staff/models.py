from django.conf import settings
from django.db import models


class StaffRoster(models.Model):
    """Cached staff roster from Google Sheets."""
    
    rank = models.CharField(max_length=50)
    rank_priority = models.IntegerField(default=999)  # Lower = higher priority
    timezone = models.CharField(max_length=50, blank=True)
    active_time = models.CharField(max_length=20, blank=True)
    name = models.CharField(max_length=100)
    steam_id = models.CharField(max_length=50, blank=True, null=True)
    discord_id = models.CharField(max_length=50, blank=True, null=True)
    discord_tag = models.CharField(max_length=100, blank=True, null=True)
    
    # Discord presence (optional - requires bot)
    discord_status = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        choices=[
            ('online', 'Online'),
            ('idle', 'Idle'),
            ('dnd', 'Do Not Disturb'),
            ('offline', 'Offline'),
        ]
    )
    discord_custom_status = models.CharField(max_length=200, blank=True, null=True)
    discord_activity = models.CharField(max_length=200, blank=True, null=True)
    discord_status_updated = models.DateTimeField(null=True, blank=True)
    
    # In-app activity tracking (fallback when Discord bot not configured)
    last_seen = models.DateTimeField(null=True, blank=True, verbose_name='Last Seen')
    is_active_in_app = models.BooleanField(default=False, verbose_name='Active in App')
    
    # Link to user account if exists
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='staff_roster'
    )
    
    # Metadata
    last_synced = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['rank_priority', 'name']  # Order by priority first, then name
        verbose_name = 'Staff Member'
        verbose_name_plural = 'Staff Roster'

    def __str__(self):
        return f"{self.name} ({self.rank})"

    @property
    def rank_color(self):
        return settings.STAFF_ROLE_COLORS.get(self.rank, '#808080')

    def get_rank_priority(self):
        """Get priority from settings for the current rank."""
        return settings.STAFF_ROLE_PRIORITIES.get(self.rank, 999)


class StaffSyncLog(models.Model):
    """Log of staff roster sync operations."""
    
    synced_at = models.DateTimeField(auto_now_add=True)
    records_synced = models.IntegerField(default=0)
    records_added = models.IntegerField(default=0)
    records_updated = models.IntegerField(default=0)
    records_removed = models.IntegerField(default=0)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ['-synced_at']

    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"Sync {self.synced_at.strftime('%Y-%m-%d %H:%M')} - {status}"
