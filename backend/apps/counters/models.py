from django.db import models
from django.conf import settings


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
