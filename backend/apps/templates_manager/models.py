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
