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
    community_banned = models.BooleanField(default=False)
    trade_ban = models.CharField(max_length=50, blank=True)
    
    # Profile status
    is_private = models.BooleanField(default=False)
    is_limited = models.BooleanField(default=False)
    level = models.IntegerField(null=True, blank=True)
    
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
