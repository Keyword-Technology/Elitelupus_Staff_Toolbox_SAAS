from django.conf import settings
from django.db import models


class Feature(models.Model):
    """Future features that can be tracked and commented on."""
    
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    title = models.CharField(max_length=200, verbose_name='Title')
    description = models.TextField(verbose_name='Description')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='planned',
        verbose_name='Status'
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name='Priority'
    )
    
    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_features',
        verbose_name='Created By'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')
    
    # Optional estimated completion
    target_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Target Date'
    )
    
    # Ordering
    order = models.IntegerField(default=0, verbose_name='Display Order')
    
    class Meta:
        ordering = ['-priority', 'order', '-created_at']
        verbose_name = 'Feature'
        verbose_name_plural = 'Features'
    
    def __str__(self):
        return self.title
    
    @property
    def comment_count(self):
        return self.comments.count()


class FeatureComment(models.Model):
    """Comments on features from any authenticated user."""
    
    feature = models.ForeignKey(
        Feature,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Feature'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='feature_comments',
        verbose_name='Author'
    )
    content = models.TextField(verbose_name='Content')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Feature Comment'
        verbose_name_plural = 'Feature Comments'
    
    def __str__(self):
        return f"Comment by {self.author.username} on {self.feature.title}"
