import logging
import os

from django.conf import settings
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


def create_or_link_user(backend, user, response, *args, **kwargs):
    """
    Custom pipeline step to create or link user accounts.
    Handles both new user creation and linking to existing accounts.
    Links Steam and Discord accounts based on staff roster data.
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
            
            # Check staff roster for Discord account with matching Steam ID
            from apps.staff.models import StaffRoster
            roster_entry = StaffRoster.objects.filter(
                steam_id=steam_id,
                is_active=True
            ).exclude(discord_id__isnull=True).exclude(discord_id='').first()
            
            if roster_entry and roster_entry.discord_id:
                # Check if a user exists with this Discord ID
                existing_user = User.objects.filter(discord_id=roster_entry.discord_id).first()
                if existing_user:
                    # Link the Steam account to the existing Discord user
                    existing_user.steam_id = steam_id
                    existing_user.steam_id_64 = steam_id_64
                    existing_user.steam_profile_url = steam_profile
                    existing_user.steam_avatar = steam_avatar
                    if not existing_user.display_name:
                        existing_user.display_name = steam_name
                    existing_user.save()
                    logger.info(f"Linked Steam account to existing Discord user {existing_user.username} via staff roster")
                    return {'user': existing_user}
            
            # Check if user exists by email (Steam doesn't provide email, so this is less common)
            # But we keep it for consistency and future Steam email support
            email = details.get('email')
            if email:
                existing_user = User.objects.filter(email__iexact=email).first()
                if existing_user:
                    # Link the Steam account to this existing user
                    existing_user.steam_id = steam_id
                    existing_user.steam_id_64 = steam_id_64
                    existing_user.steam_profile_url = steam_profile
                    existing_user.steam_avatar = steam_avatar
                    if not existing_user.display_name:
                        existing_user.display_name = steam_name
                    if not existing_user.avatar_url:
                        existing_user.avatar_url = steam_avatar
                    existing_user.save()
                    logger.info(f"Linked Steam account to existing user {existing_user.username} via email")
                    return {'user': existing_user}
            
            # Create new user - no existing user found, so create one
            user = User.objects.create_user(
                username=f"steam_{steam_id_64}",
                display_name=steam_name,
                steam_id=steam_id,
                steam_id_64=steam_id_64,
                steam_profile_url=steam_profile,
                steam_avatar=steam_avatar,
                avatar_url=steam_avatar,
                email=email,
            )
            logger.info(f"Created new user {user.username} via Steam authentication")
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
            
            # Check staff roster for Steam account with matching Discord ID
            from apps.staff.models import StaffRoster
            roster_entry = StaffRoster.objects.filter(
                discord_id=discord_id,
                is_active=True
            ).exclude(steam_id__isnull=True).exclude(steam_id='').first()
            
            if roster_entry and roster_entry.steam_id:
                # Check if a user exists with this Steam ID
                existing_user = User.objects.filter(steam_id=roster_entry.steam_id).first()
                if existing_user:
                    # Link the Discord account to the existing Steam user
                    existing_user.discord_id = discord_id
                    existing_user.discord_username = discord_username
                    existing_user.discord_discriminator = discord_discriminator
                    existing_user.discord_avatar = discord_avatar
                    if not existing_user.avatar_url:
                        existing_user.avatar_url = discord_avatar
                    existing_user.save()
                    logger.info(f"Linked Discord account to existing Steam user {existing_user.username} via staff roster")
                    return {'user': existing_user}
            
            # Check if user exists by email
            email = response.get('email')
            if email:
                existing_user = User.objects.filter(email__iexact=email).first()
                if existing_user:
                    # Link the Discord account to this existing user
                    existing_user.discord_id = discord_id
                    existing_user.discord_username = discord_username
                    existing_user.discord_discriminator = discord_discriminator
                    existing_user.discord_avatar = discord_avatar
                    if not existing_user.avatar_url:
                        existing_user.avatar_url = discord_avatar
                    existing_user.save()
                    logger.info(f"Linked Discord account to existing user {existing_user.username} via email")
                    return {'user': existing_user}
            
            # Create new user - no existing user found, so create one
            user = User.objects.create_user(
                username=f"discord_{discord_id}",
                email=email,
                display_name=discord_username,
                discord_id=discord_id,
                discord_username=discord_username,
                discord_discriminator=discord_discriminator,
                discord_avatar=discord_avatar,
                avatar_url=discord_avatar,
            )
            logger.info(f"Created new user {user.username} via Discord authentication")
            return {'user': user, 'is_new': True}
    
    return {'user': user}


def sync_staff_role(backend, user, response, *args, **kwargs):
    """
    Sync user's staff role from the Google Sheet roster.
    This runs after user creation/linking.
    """
    from social_core.exceptions import AuthForbidden
    
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
            user.is_active = True  # Activate user if in roster
            
            # Pull timezone from staff roster if available and user doesn't have one set
            if staff_data.get('timezone') and (not user.timezone or user.timezone == 'UTC'):
                user.timezone = staff_data.get('timezone')
                logger.info(f"Set timezone for {user.username} from roster: {user.timezone}")
            
            user.save()
            logger.info(f"Synced staff role for {user.username}: {user.role}")
        else:
            # Check if this is a SYSADMIN by Steam ID or Discord ID
            sysadmin_steam_ids = os.getenv('SYSADMIN_STEAM_IDS', '').split(',')
            sysadmin_discord_ids = os.getenv('SYSADMIN_DISCORD_IDS', '').split(',')
            
            is_sysadmin = (
                (user.steam_id and user.steam_id in sysadmin_steam_ids) or
                (user.steam_id_64 and str(user.steam_id_64) in sysadmin_steam_ids) or
                (user.discord_id and str(user.discord_id) in sysadmin_discord_ids)
            )
            
            if is_sysadmin:
                user.role = 'SYSADMIN'
                user.role_priority = 0
                user.is_active_staff = True
                user.is_active = True
                user.is_staff = True
                user.is_superuser = True
                user.save()
                logger.info(f"Granted SYSADMIN access to {user.username}")
            elif user.role != 'SYSADMIN':
                # Block access for non-roster, non-SYSADMIN users
                user.is_active = False
                user.is_active_staff = False
                user.save()
                logger.warning(f"User {user.username} not in staff roster - access blocked")
                # Raise an exception to prevent login and trigger error redirect
                raise AuthForbidden(
                    backend,
                    "You are not authorized to access this application. "
                    "Only staff members listed in the roster can log in. "
                    "Please contact an administrator if you believe this is an error."
                )
    except AuthForbidden:
        # Re-raise AuthForbidden - this is intentional to block non-roster users
        raise
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
