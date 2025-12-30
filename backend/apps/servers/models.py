from django.db import models


class GameServer(models.Model):
    """Configuration for monitored game servers."""
    
    name = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField()
    port = models.IntegerField()
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    
    # Server info cache
    server_name = models.CharField(max_length=200, blank=True)
    map_name = models.CharField(max_length=100, blank=True)
    max_players = models.IntegerField(default=0)
    current_players = models.IntegerField(default=0)
    
    last_query = models.DateTimeField(null=True, blank=True)
    last_successful_query = models.DateTimeField(null=True, blank=True)
    is_online = models.BooleanField(default=False)

    class Meta:
        ordering = ['display_order', 'name']
        unique_together = ['ip_address', 'port']

    def __str__(self):
        return f"{self.name} ({self.ip_address}:{self.port})"

    @property
    def address(self):
        return (self.ip_address, self.port)


class ServerPlayer(models.Model):
    """Cached player data from server queries."""
    
    server = models.ForeignKey(
        GameServer,
        on_delete=models.CASCADE,
        related_name='players'
    )
    name = models.CharField(max_length=100)
    score = models.IntegerField(default=0)
    duration = models.IntegerField(default=0)  # seconds
    
    # Link to staff if applicable
    steam_id = models.CharField(max_length=50, blank=True, null=True)
    is_staff = models.BooleanField(default=False)
    staff_rank = models.CharField(max_length=50, blank=True)
    
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-score', 'name']

    def __str__(self):
        return f"{self.name} on {self.server.name}"

    @property
    def duration_formatted(self):
        """Return formatted duration string."""
        seconds = self.duration
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"


class ServerStatusLog(models.Model):
    """Historical server status for analytics."""
    
    server = models.ForeignKey(
        GameServer,
        on_delete=models.CASCADE,
        related_name='status_logs'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    player_count = models.IntegerField()
    staff_count = models.IntegerField(default=0)
    is_online = models.BooleanField()

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['server', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.server.name} - {self.timestamp}"
