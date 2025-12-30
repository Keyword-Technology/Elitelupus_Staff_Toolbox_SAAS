from django.db import models
from django.conf import settings


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
