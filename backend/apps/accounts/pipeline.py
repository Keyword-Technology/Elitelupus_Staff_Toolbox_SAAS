import logging

from django.conf import settings
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


def create_or_link_user(backend, user, response, *args, **kwargs):
    """
    Custom pipeline step to create or link user accounts.
    Handles both new user creation and linking to existing accounts.
    """
    social = kwargs.get('social')
    is_new = kwargs.get('is_new', False)
    details = kwargs.get('details', {})
    
    if backend.name == 'steam':
        # For Steam, player data comes from details (populated by get_user_details)
        # The response is a SuccessResponse object, not a dict
        player = details.get('player', {})
        steam_id_64 = player.get('steamid') or kwargs.get('uid')
        steam_name = player.get('personaname') or details.get('username')
        steam_avatar = player.get('avatarfull') or player.get('avatar')
        steam_profile = player.get('profileurl')
        
        # Convert SteamID64 to SteamID
        steam_id = convert_steam_id_64_to_steam_id(steam_id_64)
        
        if user:
            # Link to existing user
            user.steam_id = steam_id
            user.steam_id_64 = steam_id_64
            user.steam_profile_url = steam_profile
            user.steam_avatar = steam_avatar
            if not user.display_name:
                user.display_name = steam_name
            if not user.avatar_url:
                user.avatar_url = steam_avatar
            user.save()
        else:
            # Check if user exists by steam_id
            existing_user = User.objects.filter(steam_id=steam_id).first()
            if existing_user:
                return {'user': existing_user}
            
            # Create new user
            if is_new:
                user = User.objects.create_user(
                    username=f"steam_{steam_id_64}",
                    display_name=steam_name,
                    steam_id=steam_id,
                    steam_id_64=steam_id_64,
                    steam_profile_url=steam_profile,
                    steam_avatar=steam_avatar,
                    avatar_url=steam_avatar,
                )
                return {'user': user, 'is_new': True}
    
    elif backend.name == 'discord':
        discord_id = response.get('id')
        discord_username = response.get('username')
        discord_discriminator = response.get('discriminator')
        discord_avatar_hash = response.get('avatar')
        discord_avatar = f"https://cdn.discordapp.com/avatars/{discord_id}/{discord_avatar_hash}.png" if discord_avatar_hash else None
        
        if user:
            # Link to existing user
            user.discord_id = discord_id
            user.discord_username = discord_username
            user.discord_discriminator = discord_discriminator
            user.discord_avatar = discord_avatar
            if not user.avatar_url:
                user.avatar_url = discord_avatar
            user.save()
        else:
            # Check if user exists by discord_id
            existing_user = User.objects.filter(discord_id=discord_id).first()
            if existing_user:
                return {'user': existing_user}
            
            # Create new user
            if is_new:
                user = User.objects.create_user(
                    username=f"discord_{discord_id}",
                    email=response.get('email'),
                    display_name=discord_username,
                    discord_id=discord_id,
                    discord_username=discord_username,
                    discord_discriminator=discord_discriminator,
                    discord_avatar=discord_avatar,
                    avatar_url=discord_avatar,
                )
                return {'user': user, 'is_new': True}
    
    return {'user': user}


def sync_staff_role(backend, user, response, *args, **kwargs):
    """
    Sync user's staff role from the Google Sheet roster.
    This runs after user creation/linking.
    """
    if not user:
        return
    
    from apps.staff.services import StaffSyncService
    
    try:
        # Try to sync role from Google Sheet
        sync_service = StaffSyncService()
        staff_data = sync_service.get_staff_member_data(
            steam_id=user.steam_id,
            discord_id=user.discord_id
        )
        
        if staff_data:
            user.role = staff_data.get('rank', 'User')
            user.role_priority = settings.STAFF_ROLE_PRIORITIES.get(user.role, 999)
            user.is_active_staff = True
            user.save()
            logger.info(f"Synced staff role for {user.username}: {user.role}")
    except Exception as e:
        logger.error(f"Error syncing staff role: {e}")


def convert_steam_id_64_to_steam_id(steam_id_64):
    """Convert SteamID64 to SteamID format (STEAM_X:Y:Z)."""
    try:
        steam_id_64 = int(steam_id_64)
        # SteamID64 to SteamID conversion
        # Reference: https://developer.valvesoftware.com/wiki/SteamID
        y = steam_id_64 & 1
        z = (steam_id_64 - 76561197960265728) // 2
        return f"STEAM_0:{y}:{z}"
    except (ValueError, TypeError):
        return None
