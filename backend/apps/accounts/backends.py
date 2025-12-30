from social_core.backends.discord import DiscordOAuth2 as BaseDiscordOAuth2


class DiscordOAuth2(BaseDiscordOAuth2):
    """Custom Discord OAuth2 backend."""
    
    name = 'discord'
    AUTHORIZATION_URL = 'https://discord.com/api/oauth2/authorize'
    ACCESS_TOKEN_URL = 'https://discord.com/api/oauth2/token'
    ACCESS_TOKEN_METHOD = 'POST'
    REDIRECT_STATE = False
    SCOPE_SEPARATOR = ' '
    DEFAULT_SCOPE = ['identify', 'email']
    
    def get_user_details(self, response):
        return {
            'username': response.get('username'),
            'email': response.get('email'),
            'fullname': response.get('username'),
            'first_name': response.get('username'),
        }

    def get_user_id(self, details, response):
        return response.get('id')
