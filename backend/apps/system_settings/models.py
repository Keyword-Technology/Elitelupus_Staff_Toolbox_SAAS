from django.conf import settings
from django.db import models


class SystemSetting(models.Model):
    """System-wide configuration settings that can override environment variables."""
    
    SETTING_TYPES = [
        ('string', 'String'),
        ('integer', 'Integer'),
        ('boolean', 'Boolean'),
        ('json', 'JSON'),
    ]
    
    SETTING_CATEGORIES = [
        ('general', 'General'),
        ('api_keys', 'API Keys'),
        ('database', 'Database'),
        ('cache', 'Cache'),
        ('external', 'External Services'),
        ('game_servers', 'Game Servers'),
    ]
    
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    setting_type = models.CharField(max_length=20, choices=SETTING_TYPES, default='string')
    category = models.CharField(max_length=50, choices=SETTING_CATEGORIES, default='general')
    description = models.TextField(blank=True)
    is_sensitive = models.BooleanField(default=False, help_text='If true, value will be masked in API responses')
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_settings'
    )

    class Meta:
        ordering = ['category', 'key']
        verbose_name = 'System Setting'
        verbose_name_plural = 'System Settings'

    def __str__(self):
        return f"{self.key} ({self.category})"
    
    @property
    def display_value(self):
        """Return masked value if sensitive, otherwise return actual value."""
        if self.is_sensitive and self.value:
            return '*' * 8 + self.value[-4:] if len(self.value) > 4 else '****'
        return self.value


class ManagedServer(models.Model):
    """Game servers that can be managed through the system settings."""
    
    name = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField()
    port = models.IntegerField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    
    # Optional additional config
    rcon_password = models.CharField(max_length=200, blank=True)
    query_port = models.IntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_servers'
    )

    class Meta:
        ordering = ['display_order', 'name']
        unique_together = ['ip_address', 'port']
        verbose_name = 'Managed Server'
        verbose_name_plural = 'Managed Servers'

    def __str__(self):
        return f"{self.name} ({self.ip_address}:{self.port})"
    
    @property
    def address(self):
        return f"{self.ip_address}:{self.port}"
    
    def sync_to_game_server(self):
        """Create or update the corresponding GameServer record."""
        from apps.servers.models import GameServer
        
        game_server, created = GameServer.objects.update_or_create(
            ip_address=self.ip_address,
            port=self.port,
            defaults={
                'name': self.name,
                'is_active': self.is_active,
                'display_order': self.display_order,
            }
        )
        return game_server, created


class SettingAuditLog(models.Model):
    """Audit log for tracking changes to system settings."""
    
    setting = models.ForeignKey(
        SystemSetting,
        on_delete=models.CASCADE,
        related_name='audit_logs'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    old_value = models.TextField(blank=True)
    new_value = models.TextField()
    changed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-changed_at']
        verbose_name = 'Setting Audit Log'
        verbose_name_plural = 'Setting Audit Logs'

    def __str__(self):
        return f"{self.setting.key} changed by {self.user} at {self.changed_at}"
