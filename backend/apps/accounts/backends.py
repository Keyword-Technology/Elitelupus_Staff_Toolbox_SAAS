import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from social_core.backends.discord import DiscordOAuth2 as BaseDiscordOAuth2
from social_core.backends.steam import SteamOpenId as BaseSteamOpenId

logger = logging.getLogger(__name__)
User = get_user_model()


class SteamOpenId(BaseSteamOpenId):
    """Custom Steam OpenID backend that reads API key from database system settings."""
    
    name = 'steam'
    
    def setting(self, name, default=None):
        """Override to get API_KEY from database system settings first."""
        if name == 'API_KEY':
            try:
                from apps.system_settings.models import SystemSetting
                setting = SystemSetting.objects.filter(
                    key='STEAM_API_KEY',
                    is_active=True
                ).first()
                if setting and setting.value:
                    return setting.value
            except Exception:
                pass
        
        # Fall back to default behavior
        return super().setting(name, default)


class DiscordOAuth2(BaseDiscordOAuth2):
    """Custom Discord OAuth2 backend that reads credentials from database system settings."""
    
    name = 'discord'
    AUTHORIZATION_URL = 'https://discord.com/api/oauth2/authorize'
    ACCESS_TOKEN_URL = 'https://discord.com/api/oauth2/token'
    ACCESS_TOKEN_METHOD = 'POST'
    REDIRECT_STATE = False
    SCOPE_SEPARATOR = ' '
    DEFAULT_SCOPE = ['identify', 'email']
    
    def setting(self, name, default=None):
        """Override to get KEY and SECRET from database system settings first."""
        if name == 'KEY':
            try:
                from apps.system_settings.models import SystemSetting
                setting = SystemSetting.objects.filter(
                    key='DISCORD_CLIENT_ID',
                    is_active=True
                ).first()
                if setting and setting.value:
                    return setting.value
            except Exception:
                pass
        elif name == 'SECRET':
            try:
                from apps.system_settings.models import SystemSetting
                setting = SystemSetting.objects.filter(
                    key='DISCORD_CLIENT_SECRET',
                    is_active=True
                ).first()
                if setting and setting.value:
                    return setting.value
            except Exception:
                pass
        
        # Fall back to default behavior (reads from settings.py / env vars)
        return super().setting(name, default)
    
    def get_user_details(self, response):
        return {
            'username': response.get('username'),
            'email': response.get('email'),
            'fullname': response.get('username'),
            'first_name': response.get('username'),
        }

    def get_user_id(self, details, response):
        return response.get('id')


class StaffRosterAuthenticationBackend(ModelBackend):
    """
    Custom authentication backend that validates users against the staff roster.
    SYSADMIN accounts are always allowed.
    Other accounts must be in the active staff roster.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """Authenticate user and check roster status."""
        # First, authenticate with the standard method
        user = super().authenticate(request, username, password, **kwargs)
        
        if user is None:
            return None
        
        # Check if user is active and in roster
        if not self.user_can_authenticate(user):
            logger.warning(f"Authentication failed for {username}: user inactive or not in roster")
            return None
        
        return user
    
    def user_can_authenticate(self, user):
        """
        Check if user can authenticate.
        - User must be active
        - SYSADMIN accounts are always allowed
        - Other accounts must be in active staff roster
        """
        # Check if user is active in Django
        if not user.is_active:
            return False
        
        # SYSADMIN accounts are always allowed
        if user.role == 'SYSADMIN':
            return True
        
        # Check if user is in active staff roster
        from apps.staff.services import StaffSyncService
        
        try:
            sync_service = StaffSyncService()
            return sync_service.is_user_in_roster(user)
        except Exception as e:
            logger.error(f"Error checking roster status for {user.username}: {e}")
            # On error, fall back to checking is_active_staff flag
            return user.is_active_staff
