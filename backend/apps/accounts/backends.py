from django.conf import settings
from social_core.backends.discord import DiscordOAuth2 as BaseDiscordOAuth2
from social_core.backends.steam import SteamOpenId as BaseSteamOpenId


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
