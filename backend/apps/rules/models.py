from django.db import models


class RuleCategory(models.Model):
    """Categories for rules (General, Job-Specific, etc.)"""
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    icon = models.CharField(max_length=50, blank=True)  # For frontend icons

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'Rule Categories'

    def __str__(self):
        return self.name


class Rule(models.Model):
    """Individual rules."""
    
    category = models.ForeignKey(
        RuleCategory,
        on_delete=models.CASCADE,
        related_name='rules'
    )
    code = models.CharField(max_length=20)  # e.g., "1.1", "J2.3"
    title = models.CharField(max_length=200)
    content = models.TextField()
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'order', 'code']
        unique_together = ['category', 'code']

    def __str__(self):
        return f"{self.code} - {self.title}"


class JobAction(models.Model):
    """Job-specific action permissions (can raid, can steal, etc.)"""
    
    job_name = models.CharField(max_length=100)
    category = models.CharField(max_length=100, blank=True)  # e.g., "Criminals", "Law Enforcement"
    
    can_raid = models.BooleanField(default=False)
    raid_note = models.CharField(max_length=200, blank=True)
    
    can_steal = models.BooleanField(default=False)
    steal_note = models.CharField(max_length=200, blank=True)
    
    can_mug = models.BooleanField(default=False)
    mug_note = models.CharField(max_length=200, blank=True)
    
    can_kidnap = models.BooleanField(default=False)
    kidnap_note = models.CharField(max_length=200, blank=True)
    
    can_base = models.BooleanField(default=False)
    base_note = models.CharField(max_length=200, blank=True)
    
    can_have_printers = models.BooleanField(default=False)
    printers_note = models.CharField(max_length=200, blank=True)
    
    additional_notes = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['category', 'order', 'job_name']

    def __str__(self):
        return self.job_name
