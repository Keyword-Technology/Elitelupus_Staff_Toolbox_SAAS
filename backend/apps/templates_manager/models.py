from django.conf import settings
from django.db import models
from django.utils import timezone


class SteamProfileSearch(models.Model):
    """Track Steam profile searches."""
    
    steam_id_64 = models.CharField(max_length=50, db_index=True)
    steam_id = models.CharField(max_length=50, blank=True)
    
    # Search tracking
    search_count = models.IntegerField(default=1)
    first_searched_at = models.DateTimeField(auto_now_add=True)
    last_searched_at = models.DateTimeField(auto_now=True)
    last_searched_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='steam_searches'
    )
    
    # Latest profile data
    persona_name = models.CharField(max_length=255, blank=True)
    profile_url = models.URLField(blank=True)
    avatar_url = models.URLField(blank=True)
    profile_state = models.CharField(max_length=20, blank=True)
    real_name = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=100, blank=True)
    
    # Additional Steam profile data
    steam_id_3 = models.CharField(max_length=50, blank=True, verbose_name='SteamID3')
    custom_url = models.CharField(max_length=255, blank=True, verbose_name='Custom URL')
    persona_state = models.IntegerField(default=0, verbose_name='Persona State')  # 0=Offline, 1=Online, etc.
    persona_state_flags = models.IntegerField(default=0, blank=True)
    last_logoff = models.DateTimeField(null=True, blank=True)
    comment_permission = models.BooleanField(default=False)
    
    # Game info
    game_id = models.CharField(max_length=50, blank=True)
    game_server_ip = models.CharField(max_length=50, blank=True)
    game_extra_info = models.CharField(max_length=255, blank=True)
    
    # Country info
    country_code = models.CharField(max_length=10, blank=True)
    state_code = models.CharField(max_length=10, blank=True)
    city_id = models.IntegerField(null=True, blank=True)
    
    # Extended data from steamid.io / steamid.pro
    account_created = models.DateTimeField(null=True, blank=True)
    vac_bans = models.IntegerField(default=0)
    game_bans = models.IntegerField(default=0)
    days_since_last_ban = models.IntegerField(null=True, blank=True)
    vac_ban_dates = models.JSONField(default=list, blank=True, help_text='List of VAC ban dates from steamid.pro')
    community_banned = models.BooleanField(default=False)
    trade_ban = models.CharField(max_length=50, blank=True)
    
    # Profile status
    is_private = models.BooleanField(default=False)
    is_limited = models.BooleanField(default=False)
    level = models.IntegerField(null=True, blank=True)
    
    # Enhanced scraped data from steamid.pro and steamid.io
    account_name = models.CharField(max_length=255, blank=True, help_text='Steam account login name (from steamid.io)')
    vanity_url = models.CharField(max_length=255, blank=True, help_text='Custom vanity URL')
    account_id = models.CharField(max_length=50, blank=True, help_text='Steam Account ID')
    steam_id_2 = models.CharField(max_length=50, blank=True, help_text='Steam2 ID format')
    invite_url = models.URLField(blank=True, help_text='Steam invite URL')
    invite_url_short = models.URLField(blank=True, help_text='Short Steam invite URL')
    fivem_hex = models.CharField(max_length=50, blank=True, help_text='FiveM HEX identifier')
    online_status = models.CharField(max_length=20, blank=True, help_text='Current online status')
    estimated_value = models.CharField(max_length=50, blank=True, help_text='Estimated account value')
    rating_value = models.FloatField(null=True, blank=True, help_text='Community rating value')
    rating_count = models.IntegerField(null=True, blank=True, help_text='Number of ratings')
    scraped_description = models.TextField(blank=True, help_text='Profile description from scraper')
    last_scraped_at = models.DateTimeField(null=True, blank=True, help_text='When profile was last scraped')
    scrape_data = models.JSONField(default=dict, blank=True, help_text='Raw scraped data')
    
    # Past names tracking
    past_names = models.JSONField(default=list, blank=True, help_text='List of past display names with timestamps')
    
    class Meta:
        ordering = ['-last_searched_at']
        verbose_name = 'Steam Profile Search'
        verbose_name_plural = 'Steam Profile Searches'
    
    def __str__(self):
        return f"{self.persona_name or self.steam_id_64} ({self.search_count} searches)"


class SteamProfileHistory(models.Model):
    """Track changes to Steam profiles over time."""
    
    search = models.ForeignKey(
        SteamProfileSearch,
        on_delete=models.CASCADE,
        related_name='history'
    )
    searched_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    searched_at = models.DateTimeField(auto_now_add=True)
    
    # Snapshot of profile data at search time
    persona_name = models.CharField(max_length=255, blank=True)
    avatar_url = models.URLField(blank=True)
    profile_state = models.CharField(max_length=20, blank=True)
    vac_bans = models.IntegerField(default=0)
    game_bans = models.IntegerField(default=0)
    days_since_last_ban = models.IntegerField(null=True, blank=True)
    
    # Track what changed
    changes_detected = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-searched_at']
        verbose_name = 'Steam Profile History'
        verbose_name_plural = 'Steam Profile Histories'
    
    def __str__(self):
        return f"{self.search.steam_id_64} - {self.searched_at}"


class RefundTemplate(models.Model):
    """Template for tracking refund requests."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('denied', 'Denied'),
        ('completed', 'Completed'),
    ]
    
    # Owner/Creator
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='refund_templates'
    )
    
    # Ticket Info
    ticket_number = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Player Info
    player_ign = models.CharField(max_length=100, verbose_name='In-Game Name')
    steam_id = models.CharField(max_length=50)
    steam_id_64 = models.CharField(max_length=50, blank=True)
    steam_profile = models.ForeignKey(
        SteamProfileSearch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='refund_templates'
    )
    server = models.CharField(max_length=50, choices=[
        ('OG', 'OG Server'),
        ('Normal', 'Normal Server'),
    ])
    
    # Refund Details
    items_lost = models.TextField()
    reason = models.TextField()
    evidence = models.TextField(blank=True)
    
    # Resolution
    refund_amount = models.CharField(max_length=100, blank=True)
    admin_notes = models.TextField(blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_refunds'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.ticket_number} - {self.player_ign}"


class TemplateCategory(models.Model):
    """Categories for response templates."""
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'Template Categories'

    def __str__(self):
        return self.name


class ResponseTemplate(models.Model):
    """Pre-defined response templates for common situations."""
    
    category = models.ForeignKey(
        TemplateCategory,
        on_delete=models.CASCADE,
        related_name='templates'
    )
    name = models.CharField(max_length=100)
    content = models.TextField()
    variables = models.JSONField(default=list, blank=True)  # List of variable names
    is_active = models.BooleanField(default=True)
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_templates'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.category.name} - {self.name}"


class BanExtensionTemplate(models.Model):
    """Template for ban extension requests."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('denied', 'Denied'),
    ]
    
    # Staff Member who submitted
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ban_extensions'
    )
    
    # Player Information
    player_ign = models.CharField(max_length=100, verbose_name='In-Game Name')
    steam_id = models.CharField(max_length=50)
    steam_id_64 = models.CharField(max_length=50, blank=True)
    steam_profile = models.ForeignKey(
        SteamProfileSearch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ban_extensions'
    )
    
    # Server & Ban Details
    server_number = models.CharField(max_length=10)
    ban_reason = models.TextField()
    current_ban_time = models.CharField(max_length=100)
    required_ban_time = models.CharField(max_length=100)
    extension_reason = models.TextField()
    
    # Status & Resolution
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_ban_extensions'
    )
    admin_notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ban_expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Ban Extension'
        verbose_name_plural = 'Ban Extensions'

    def __str__(self):
        return f"{self.player_ign} - {self.ban_reason[:50]}"
    
    @property
    def is_active_ban(self):
        """Check if ban is still active."""
        if self.ban_expires_at and self.status == 'approved':
            return timezone.now() < self.ban_expires_at
        return False


class PlayerReportTemplate(models.Model):
    """Template for player reports (accepted/denied)."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('accepted', 'Accepted'),
        ('denied', 'Denied'),
    ]
    
    ACTION_CHOICES = [
        ('none', 'No Action'),
        ('warned', 'Warned'),
        ('banned', 'Banned'),
        ('kicked', 'Kicked'),
    ]
    
    # Staff handling the report
    handled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='handled_reports'
    )
    
    # Reported Player
    player_ign = models.CharField(max_length=100, verbose_name='Reported Player IGN')
    steam_id = models.CharField(max_length=50)
    steam_id_64 = models.CharField(max_length=50, blank=True)
    steam_profile = models.ForeignKey(
        SteamProfileSearch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='player_reports'
    )
    
    # Report Details
    case_link = models.URLField(verbose_name='Discord Case Transcript Link')
    report_reason = models.TextField()
    evidence_provided = models.TextField(blank=True)
    
    # Decision
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    decision_reason = models.TextField()
    action_taken = models.CharField(max_length=20, choices=ACTION_CHOICES, default='none')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Player Report'
        verbose_name_plural = 'Player Reports'

    def __str__(self):
        return f"{self.player_ign} - {self.status}"


class StaffApplicationResponse(models.Model):
    """Template for staff application reviews."""
    
    RATING_CHOICES = [(i, f"{i}/5") for i in range(1, 6)]
    
    # Reviewer
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='staff_reviews'
    )
    
    # Applicant Information
    applicant_name = models.CharField(max_length=100)
    steam_id_64 = models.CharField(max_length=50, blank=True)
    steam_profile = models.ForeignKey(
        SteamProfileSearch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='staff_applications'
    )
    discord_username = models.CharField(max_length=100, blank=True)
    
    # Review Content
    positive_rep = models.TextField(verbose_name='+ Rep')
    neutral_rep = models.TextField(blank=True, verbose_name='+/- Rep')
    negative_rep = models.TextField(blank=True, verbose_name='- Rep')
    overall_comment = models.TextField()
    
    # Rating
    rating = models.IntegerField(choices=RATING_CHOICES, default=3)
    
    # Decision
    recommend_hire = models.BooleanField(default=False)
    recommended_role = models.CharField(max_length=50, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Staff Application Response'
        verbose_name_plural = 'Staff Application Responses'

    def __str__(self):
        return f"{self.applicant_name} - {self.rating}/5"
    
    @property
    def rating_stars(self):
        """Return star representation of rating."""
        filled = '★' * self.rating
        empty = '☆' * (5 - self.rating)
        return f"{filled}{empty}"


class TemplateComment(models.Model):
    """Comments/annotations on filled templates."""
    
    TEMPLATE_TYPE_CHOICES = [
        ('refund', 'Refund'),
        ('ban_extension', 'Ban Extension'),
        ('player_report', 'Player Report'),
        ('staff_application', 'Staff Application'),
    ]
    
    # Comment author
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='template_comments'
    )
    
    # What template type and ID
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPE_CHOICES)
    template_id = models.IntegerField()
    
    # Comment content
    comment = models.TextField()
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Template Comment'
        verbose_name_plural = 'Template Comments'
        indexes = [
            models.Index(fields=['template_type', 'template_id']),
        ]
    
    def __str__(self):
        return f"Comment by {self.author.username} on {self.template_type} #{self.template_id}"


class SteamProfileNote(models.Model):
    """Admin notes and warnings for Steam profiles."""
    
    NOTE_TYPE_CHOICES = [
        ('general', 'General Note'),
        ('warning_verbal', 'Verbal Warning'),
        ('warning_written', 'Written Warning'),
        ('ban_history', 'Ban History'),
        ('behavior', 'Behavior Note'),
        ('investigation', 'Under Investigation'),
    ]
    
    # Steam profile this note is for
    steam_profile = models.ForeignKey(
        SteamProfileSearch,
        on_delete=models.CASCADE,
        related_name='notes'
    )
    
    # Note author
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='steam_notes'
    )
    
    # Note details
    note_type = models.CharField(max_length=20, choices=NOTE_TYPE_CHOICES, default='general')
    title = models.CharField(max_length=255, blank=True)
    content = models.TextField()
    
    # For warnings - track if resolved
    is_active = models.BooleanField(default=True, help_text='For warnings, marks if still active')
    severity = models.IntegerField(
        default=1, 
        choices=[(1, 'Low'), (2, 'Medium'), (3, 'High'), (4, 'Critical')],
        help_text='Severity level of the note/warning'
    )
    
    # Server context
    server = models.CharField(max_length=50, blank=True, help_text='Server where incident occurred')
    incident_date = models.DateTimeField(null=True, blank=True, help_text='When the incident occurred')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Optional: Mark as resolved/expired
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_steam_notes'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Steam Profile Note'
        verbose_name_plural = 'Steam Profile Notes'
        indexes = [
            models.Index(fields=['steam_profile', 'note_type']),
            models.Index(fields=['is_active', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_note_type_display()} for {self.steam_profile.persona_name} by {self.author.username}"
    
    @property
    def warning_count(self):
        """Get count of warnings for this profile."""
        return self.steam_profile.notes.filter(
            note_type__in=['warning_verbal', 'warning_written'],
            is_active=True
        ).count()


class SteamProfileBookmark(models.Model):
    """Bookmarked Steam profiles for quick access."""
    
    # User who bookmarked
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='steam_bookmarks'
    )
    
    # Steam profile that's bookmarked
    steam_profile = models.ForeignKey(
        SteamProfileSearch,
        on_delete=models.CASCADE,
        related_name='bookmarks'
    )
    
    # Optional note for why bookmarked
    note = models.CharField(max_length=255, blank=True)
    
    # Tags for organization
    tags = models.JSONField(default=list, blank=True, help_text='List of tags like ["suspicious", "frequent player"]')
    
    # Pin to top
    is_pinned = models.BooleanField(default=False, help_text='Pin this bookmark to the top')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_pinned', '-created_at']
        unique_together = ['user', 'steam_profile']
        verbose_name = 'Steam Profile Bookmark'
        verbose_name_plural = 'Steam Profile Bookmarks'
        indexes = [
            models.Index(fields=['user', 'is_pinned']),
        ]
    
    def __str__(self):
        return f"{self.user.username} bookmarked {self.steam_profile.persona_name}"
