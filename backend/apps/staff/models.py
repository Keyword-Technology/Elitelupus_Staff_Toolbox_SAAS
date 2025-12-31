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


class ServerSession(models.Model):
    """Track individual staff member server sessions."""
    
    staff = models.ForeignKey(
        StaffRoster,
        on_delete=models.CASCADE,
        related_name='server_sessions',
        verbose_name='Staff Member'
    )
    server = models.ForeignKey(
        'servers.GameServer',
        on_delete=models.CASCADE,
        related_name='staff_sessions',
        verbose_name='Server'
    )
    
    # Session timing
    join_time = models.DateTimeField(verbose_name='Join Time')
    leave_time = models.DateTimeField(null=True, blank=True, verbose_name='Leave Time')
    duration = models.IntegerField(default=0, verbose_name='Duration (seconds)')
    
    # Additional metadata
    steam_id = models.CharField(max_length=50, blank=True, null=True)
    player_name = models.CharField(max_length=100, blank=True)
    
    # Auto-updated
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-join_time']
        indexes = [
            models.Index(fields=['staff', 'join_time']),
            models.Index(fields=['server', 'join_time']),
            models.Index(fields=['steam_id', 'join_time']),
        ]
        verbose_name = 'Server Session'
        verbose_name_plural = 'Server Sessions'
    
    def __str__(self):
        return f"{self.staff.name} on {self.server.name} at {self.join_time}"
    
    def calculate_duration(self):
        """Calculate and update session duration."""
        if self.leave_time and self.join_time:
            delta = self.leave_time - self.join_time
            self.duration = int(delta.total_seconds())
        return self.duration
    
    @property
    def duration_formatted(self):
        """Return formatted duration string."""
        if not self.duration:
            return "Active"
        
        hours = self.duration // 3600
        minutes = (self.duration % 3600) // 60
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"
    
    @property
    def is_active(self):
        """Check if session is currently active."""
        return self.leave_time is None


class ServerSessionAggregate(models.Model):
    """Pre-computed statistics for staff server time."""
    
    PERIOD_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('all_time', 'All Time'),
    ]
    
    staff = models.ForeignKey(
        StaffRoster,
        on_delete=models.CASCADE,
        related_name='session_aggregates',
        verbose_name='Staff Member'
    )
    server = models.ForeignKey(
        'servers.GameServer',
        on_delete=models.CASCADE,
        related_name='staff_aggregates',
        verbose_name='Server',
        null=True,
        blank=True  # null means all servers
    )
    
    # Time period
    period_type = models.CharField(max_length=20, choices=PERIOD_CHOICES, default='daily')
    period_start = models.DateField(verbose_name='Period Start')
    period_end = models.DateField(null=True, blank=True, verbose_name='Period End')
    
    # Aggregated statistics
    total_time = models.IntegerField(default=0, verbose_name='Total Time (seconds)')
    session_count = models.IntegerField(default=0, verbose_name='Session Count')
    avg_session_time = models.IntegerField(default=0, verbose_name='Average Session Time (seconds)')
    longest_session = models.IntegerField(default=0, verbose_name='Longest Session (seconds)')
    
    # Timestamps
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-period_start']
        unique_together = ['staff', 'server', 'period_type', 'period_start']
        indexes = [
            models.Index(fields=['staff', 'period_type', 'period_start']),
            models.Index(fields=['server', 'period_type', 'period_start']),
        ]
        verbose_name = 'Session Aggregate'
        verbose_name_plural = 'Session Aggregates'
    
    def __str__(self):
        server_name = self.server.name if self.server else "All Servers"
        return f"{self.staff.name} on {server_name} - {self.period_type} ({self.period_start})"
    
    @property
    def total_time_formatted(self):
        """Return formatted total time string."""
        hours = self.total_time // 3600
        minutes = (self.total_time % 3600) // 60
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"
    
    @property
    def avg_session_time_formatted(self):
        """Return formatted average session time string."""
        hours = self.avg_session_time // 3600
        minutes = (self.avg_session_time % 3600) // 60
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"


class StaffHistoryEvent(models.Model):
    """Track staff member history events (joins, promotions, demotions, removals)."""
    
    EVENT_TYPES = [
        ('joined', 'Joined Staff'),
        ('promoted', 'Promoted'),
        ('demoted', 'Demoted'),
        ('role_change', 'Role Changed'),
        ('left', 'Left Staff'),
        ('removed', 'Demoted'),
        ('rejoined', 'Rejoined Staff'),
    ]
    
    staff = models.ForeignKey(
        StaffRoster,
        on_delete=models.CASCADE,
        related_name='history_events',
        verbose_name='Staff Member'
    )
    
    event_type = models.CharField(
        max_length=20,
        choices=EVENT_TYPES,
        verbose_name='Event Type'
    )
    
    # Role information
    old_rank = models.CharField(max_length=50, blank=True, null=True, verbose_name='Old Rank')
    new_rank = models.CharField(max_length=50, blank=True, null=True, verbose_name='New Rank')
    old_rank_priority = models.IntegerField(null=True, blank=True, verbose_name='Old Rank Priority')
    new_rank_priority = models.IntegerField(null=True, blank=True, verbose_name='New Rank Priority')
    
    # Event metadata
    event_date = models.DateTimeField(verbose_name='Event Date')
    notes = models.TextField(blank=True, verbose_name='Notes')
    
    # Auto-detected or manual
    auto_detected = models.BooleanField(default=True, verbose_name='Auto Detected')
    
    # Created by (for manual entries)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='staff_events_created',
        verbose_name='Created By'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-event_date']
        indexes = [
            models.Index(fields=['staff', 'event_date']),
            models.Index(fields=['event_type', 'event_date']),
        ]
        verbose_name = 'Staff History Event'
        verbose_name_plural = 'Staff History Events'
    
    def __str__(self):
        return f"{self.staff.name} - {self.get_event_type_display()} on {self.event_date.strftime('%Y-%m-%d')}"
    
    @property
    def is_promotion(self):
        """Check if this is a promotion (lower priority = higher rank)."""
        if self.event_type in ['promoted', 'role_change'] and self.old_rank_priority and self.new_rank_priority:
            return self.new_rank_priority < self.old_rank_priority
        return self.event_type == 'promoted'
    
    @property
    def is_demotion(self):
        """Check if this is a demotion (higher priority = lower rank)."""
        if self.event_type in ['demoted', 'role_change'] and self.old_rank_priority and self.new_rank_priority:
            return self.new_rank_priority > self.old_rank_priority
        return self.event_type == 'demoted'
    
    @property
    def event_description(self):
        """Generate human-readable event description."""
        if self.event_type == 'joined':
            return f"Joined as {self.new_rank}"
        elif self.event_type == 'rejoined':
            return f"Rejoined as {self.new_rank}"
        elif self.event_type in ['promoted', 'demoted', 'role_change']:
            if self.old_rank and self.new_rank:
                return f"{self.old_rank} → {self.new_rank}"
            return self.get_event_type_display()
        elif self.event_type in ['left', 'removed']:
            return f"Left staff (was {self.old_rank})" if self.old_rank else "Left staff"
        return self.get_event_type_display()
