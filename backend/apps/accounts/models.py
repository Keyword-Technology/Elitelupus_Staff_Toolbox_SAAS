import pytz
from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """Custom user manager for User model."""

    def create_user(self, username, email=None, password=None, **extra_fields):
        """Create and save a regular user."""
        if not username:
            raise ValueError('Users must have a username')
        
        email = self.normalize_email(email) if email else None
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        """Create and save a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'SYSADMIN')
        extra_fields.setdefault('role_priority', 0)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, email, password, **extra_fields)


TIMEZONE_CHOICES = [(tz, tz) for tz in pytz.common_timezones]


class User(AbstractUser):
    """Custom User model with staff roles and social auth links."""
    
    ROLE_CHOICES = [
        ('SYSADMIN', 'System Administrator'),
        ('Manager', 'Manager'),
        ('Staff Manager', 'Staff Manager'),
        ('Assistant Staff Manager', 'Assistant Staff Manager'),
        ('Meta Manager', 'Meta Manager'),
        ('Event Manager', 'Event Manager'),
        ('Senior Admin', 'Senior Admin'),
        ('Admin', 'Admin'),
        ('Senior Moderator', 'Senior Moderator'),
        ('Moderator', 'Moderator'),
        ('Senior Operator', 'Senior Operator'),
        ('Operator', 'Operator'),
        ('T-Staff', 'T-Staff'),
        ('User', 'User'),
    ]

    # Basic Info
    email = models.EmailField('email address', blank=True, null=True)
    display_name = models.CharField(max_length=100, blank=True)
    avatar_url = models.URLField(blank=True, null=True)
    
    # Role Management
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='User')
    role_priority = models.IntegerField(default=999)  # Lower number = higher priority
    
    # Steam Integration
    steam_id = models.CharField(max_length=50, blank=True, null=True, unique=True)
    steam_id_64 = models.CharField(max_length=50, blank=True, null=True)
    steam_profile_url = models.URLField(blank=True, null=True)
    steam_avatar = models.URLField(blank=True, null=True)
    
    # Discord Integration
    discord_id = models.CharField(max_length=50, blank=True, null=True, unique=True)
    discord_username = models.CharField(max_length=100, blank=True, null=True)
    discord_discriminator = models.CharField(max_length=10, blank=True, null=True)
    discord_avatar = models.URLField(blank=True, null=True)
    
    # Timezone Support
    timezone = models.CharField(
        max_length=50,
        choices=TIMEZONE_CHOICES,
        default='UTC'
    )
    
    # Display Preferences
    use_24_hour_time = models.BooleanField(
        default=True,
        verbose_name='Use 24-hour time format',
        help_text='Display times in 24-hour format instead of 12-hour AM/PM'
    )
    
    # Staff Metadata
    is_active_staff = models.BooleanField(default=False)
    is_legacy_staff = models.BooleanField(default=False)  # Former staff not in roster
    staff_since = models.DateTimeField(null=True, blank=True)
    staff_left_at = models.DateTimeField(null=True, blank=True)  # When removed from roster
    
    # Timestamps
    last_activity = models.DateTimeField(null=True, blank=True)
    
    objects = UserManager()

    class Meta:
        ordering = ['role_priority', 'username']

    def __str__(self):
        return f"{self.display_name or self.username} ({self.role})"

    @property
    def role_color(self):
        """Return the color associated with the user's role."""
        return settings.STAFF_ROLE_COLORS.get(self.role, '#808080')

    def has_permission_over(self, other_user):
        """Check if this user has permission over another user based on role priority."""
        return self.role_priority < other_user.role_priority

    def can_manage_role(self, role):
        """Check if user can manage users with a specific role."""
        target_priority = settings.STAFF_ROLE_PRIORITIES.get(role, 999)
        return self.role_priority < target_priority

    def save(self, *args, **kwargs):
        # Auto-set role priority based on role
        if self.role in settings.STAFF_ROLE_PRIORITIES:
            self.role_priority = settings.STAFF_ROLE_PRIORITIES[self.role]
        super().save(*args, **kwargs)


class SocialAccountLink(models.Model):
    """Track social account linking requests and history."""
    
    PROVIDER_CHOICES = [
        ('steam', 'Steam'),
        ('discord', 'Discord'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('linked', 'Linked'),
        ('unlinked', 'Unlinked'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_links')
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    provider_id = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    linked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['provider', 'provider_id']

    def __str__(self):
        return f"{self.user.username} - {self.provider} ({self.status})"
