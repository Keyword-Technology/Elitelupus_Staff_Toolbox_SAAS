import uuid

from django.conf import settings
from django.db import models


class Counter(models.Model):
    """User-specific counter for sits and tickets."""
    
    COUNTER_TYPES = [
        ('sit', 'Sit'),
        ('ticket', 'Ticket'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='counters'
    )
    counter_type = models.CharField(max_length=20, choices=COUNTER_TYPES)
    count = models.IntegerField(default=0)
    
    # Track period (daily, weekly, monthly, total)
    period_start = models.DateField(null=True, blank=True)
    period_type = models.CharField(max_length=20, default='total')  # daily, weekly, monthly, total
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'counter_type', 'period_type', 'period_start']
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username} - {self.counter_type}: {self.count}"


class CounterHistory(models.Model):
    """History of counter changes for tracking and analytics."""
    
    ACTION_CHOICES = [
        ('increment', 'Increment'),
        ('decrement', 'Decrement'),
        ('set', 'Set Value'),
        ('reset', 'Reset'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='counter_history'
    )
    counter_type = models.CharField(max_length=20)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    old_value = models.IntegerField()
    new_value = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Optional note for context
    note = models.TextField(blank=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Counter History'

    def __str__(self):
        return f"{self.user.username} - {self.counter_type}: {self.old_value} -> {self.new_value}"


class CounterSnapshot(models.Model):
    """Daily snapshots of counters for reporting."""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='counter_snapshots'
    )
    date = models.DateField()
    sit_count = models.IntegerField(default=0)
    ticket_count = models.IntegerField(default=0)

    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username} - {self.date}: Sits={self.sit_count}, Tickets={self.ticket_count}"


# ============================================================================
# SIT RECORDING SYSTEM - New models for screen recording and OCR detection
# ============================================================================

class Sit(models.Model):
    """
    A recorded sit session with optional screen recording.
    Links to the legacy counter system for sit counting.
    """
    
    OUTCOME_CHOICES = [
        ('no_action', 'No Action Taken'),
        ('false_report', 'False Report'),
        ('verbal_warning', 'Verbal Warning'),
        ('formal_warning', 'Formal Warning'),
        ('kick', 'Kick'),
        ('ban', 'Ban'),
        ('escalated', 'Escalated to Higher Staff'),
        ('other', 'Other'),
    ]
    
    REPORT_TYPE_CHOICES = [
        ('rdm', 'RDM'),
        ('nlr', 'NLR'),
        ('rda', 'RDA'),
        ('failrp', 'FailRP'),
        ('propblock', 'Prop Block/Abuse'),
        ('harassment', 'Harassment'),
        ('other', 'Other'),
    ]
    
    DETECTION_METHOD_CHOICES = [
        ('manual', 'Manual (Button Click)'),
        ('ocr_chat', 'OCR - Chat Detection'),
        ('ocr_popup', 'OCR - Popup Detection'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Staff member handling the sit
    staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sits'
    )
    
    # Report details (extracted from OCR or manual entry)
    reporter_name = models.CharField(max_length=100, blank=True)
    reported_player = models.CharField(max_length=100, blank=True)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPE_CHOICES, blank=True)
    report_reason = models.TextField(blank=True)
    
    # Timing
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True)
    
    # Outcome
    outcome = models.CharField(max_length=50, choices=OUTCOME_CHOICES, blank=True)
    outcome_notes = models.TextField(blank=True)
    ban_duration = models.CharField(max_length=50, blank=True)  # e.g., "1 day", "permanent"
    
    # Staff rating (from player feedback via [Elite Admin Stats])
    player_rating = models.IntegerField(null=True, blank=True)  # 1-5 stars
    player_rating_credits = models.IntegerField(null=True, blank=True)  # 0, 2, 4, 6, 8
    
    # Detection method
    detection_method = models.CharField(
        max_length=20, 
        choices=DETECTION_METHOD_CHOICES, 
        default='manual'
    )
    
    # Recording info
    has_recording = models.BooleanField(default=False)
    recording_file = models.FileField(
        upload_to='sit_recordings/%Y/%m/%d/',
        null=True,
        blank=True
    )
    recording_size_bytes = models.BigIntegerField(null=True, blank=True)
    recording_duration_seconds = models.IntegerField(null=True, blank=True)
    
    # Thumbnail for video preview
    recording_thumbnail = models.ImageField(
        upload_to='sit_thumbnails/%Y/%m/%d/',
        null=True,
        blank=True
    )
    
    # Link to legacy counter (if sit was counted)
    counter_history = models.ForeignKey(
        'CounterHistory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sit_record'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Sit'
        verbose_name_plural = 'Sits'
    
    def __str__(self):
        return f"{self.staff.username} - {self.reporter_name or 'Unknown'} ({self.started_at.strftime('%Y-%m-%d %H:%M')})"
    
    def save(self, *args, **kwargs):
        # Calculate duration if both times are set
        if self.started_at and self.ended_at:
            delta = self.ended_at - self.started_at
            self.duration_seconds = int(delta.total_seconds())
        super().save(*args, **kwargs)


class SitNote(models.Model):
    """
    Notes attached to a sit, including Steam IDs of involved players.
    """
    
    NOTE_TYPE_CHOICES = [
        ('general', 'General Note'),
        ('steam_id', 'Steam ID'),
        ('evidence', 'Evidence'),
        ('action', 'Action Taken'),
    ]
    
    sit = models.ForeignKey(
        Sit,
        on_delete=models.CASCADE,
        related_name='notes'
    )
    note_type = models.CharField(max_length=20, choices=NOTE_TYPE_CHOICES, default='general')
    content = models.TextField()
    
    # For Steam ID notes
    steam_id = models.CharField(max_length=50, blank=True)
    steam_profile_url = models.URLField(blank=True)
    steam_persona_name = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sit.id} - {self.note_type}: {self.content[:50]}"


class SitRecordingChunk(models.Model):
    """
    For chunked uploads of large recordings.
    Allows resumable uploads and progress tracking.
    """
    
    sit = models.ForeignKey(
        Sit,
        on_delete=models.CASCADE,
        related_name='recording_chunks'
    )
    chunk_number = models.IntegerField()
    chunk_file = models.FileField(upload_to='sit_recording_chunks/')
    size_bytes = models.IntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['sit', 'chunk_number']
        ordering = ['chunk_number']
    
    def __str__(self):
        return f"{self.sit.id} - Chunk {self.chunk_number}"


class UserSitPreferences(models.Model):
    """
    User preferences for the sit recording system.
    Allows users to enable/disable the feature individually.
    """
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sit_preferences'
    )
    
    # Feature toggles
    recording_enabled = models.BooleanField(
        default=True,
        help_text='Enable screen recording during sits'
    )
    ocr_enabled = models.BooleanField(
        default=True,
        help_text='Enable OCR auto-detection of sit events'
    )
    auto_start_recording = models.BooleanField(
        default=True,
        help_text='Automatically start recording when sit is detected'
    )
    auto_stop_recording = models.BooleanField(
        default=True,
        help_text='Automatically stop recording when sit is closed'
    )
    
    # OCR Settings
    ocr_scan_interval_ms = models.IntegerField(
        default=1500,
        help_text='Milliseconds between OCR scans'
    )
    ocr_popup_region_enabled = models.BooleanField(
        default=True,
        help_text='Scan report popup area for detection'
    )
    ocr_chat_region_enabled = models.BooleanField(
        default=True,
        help_text='Scan chat area for detection'
    )
    
    # Recording Settings
    video_quality = models.CharField(
        max_length=20,
        default='medium',
        choices=[
            ('low', 'Low (1 Mbps)'),
            ('medium', 'Medium (2.5 Mbps)'),
            ('high', 'High (5 Mbps)'),
        ]
    )
    max_recording_minutes = models.IntegerField(
        default=30,
        help_text='Maximum recording duration in minutes'
    )
    
    # UI Settings
    show_recording_preview = models.BooleanField(
        default=True,
        help_text='Show small preview of recording in UI'
    )
    confirm_before_start = models.BooleanField(
        default=False,
        help_text='Show confirmation popup before auto-starting recording'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Sit Preferences'
        verbose_name_plural = 'User Sit Preferences'
    
    def __str__(self):
        return f"{self.user.username} - Sit Preferences"
