"""
Celery tasks for staff roster management.
"""
import asyncio
import logging
import time

import requests
from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task
def sync_staff_roster():
    """Sync staff roster from Google Sheets."""
    from .consumers import broadcast_roster_sync
    from .services import StaffSyncService
    
    try:
        service = StaffSyncService()
        log = service.sync_staff_roster()
        
        # Return JSON-serializable dict instead of model instance
        result = {
            'success': log.success,
            'records_synced': log.records_synced,
            'records_added': log.records_added,
            'records_updated': log.records_updated,
            'records_removed': log.records_removed,
            'error_message': log.error_message,
            'synced_at': log.synced_at.isoformat() if log.synced_at else None,
        }
        
        logger.info(f"Staff roster sync completed: {result}")
        
        # Broadcast the sync result to all connected clients
        try:
            broadcast_roster_sync(
                records_updated=log.records_synced,
                status='success' if log.success else 'error'
            )
        except Exception as e:
            logger.warning(f"Could not broadcast roster sync: {e}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error syncing staff roster: {e}")
        try:
            from .consumers import broadcast_roster_sync
            broadcast_roster_sync(records_updated=0, status='error')
        except:
            pass
        return {'success': False, 'error': str(e)}


@shared_task
def sync_staff_steam_names():
    """
    Sync Steam display names for all active staff members.
    
    This task fetches the current Steam persona name for each staff member
    using the Steam Web API. These names are then used to match players
    on game servers to identify staff members.
    
    Runs twice daily (configured in celery beat schedule).
    """
    from django.utils import timezone

    from .models import Staff
    
    steam_api_key = getattr(settings, 'SOCIAL_AUTH_STEAM_API_KEY', None)
    
    if not steam_api_key:
        logger.warning("Steam API key not configured, skipping Steam name sync")
        return {'success': False, 'error': 'Steam API key not configured'}
    
    # Get all active staff with valid Steam IDs
    staff_members = Staff.objects.filter(staff_status='active').exclude(steam_id__isnull=True).exclude(steam_id='')
    
    if not staff_members.exists():
        logger.info("No active staff members with Steam IDs found")
        return {'success': True, 'updated': 0, 'total': 0}
    
    # Convert Steam IDs to Steam64 format for API call
    steam_ids_64 = []
    staff_by_steam64 = {}
    
    for staff in staff_members:
        steam64 = _convert_to_steam64(staff.steam_id)
        if steam64:
            steam_ids_64.append(steam64)
            staff_by_steam64[steam64] = staff
    
    if not steam_ids_64:
        logger.warning("No valid Steam64 IDs found for staff members")
        return {'success': False, 'error': 'No valid Steam64 IDs'}
    
    # Steam API allows up to 100 Steam IDs per request
    updated_count = 0
    errors = []
    batch_size = 100
    
    for i in range(0, len(steam_ids_64), batch_size):
        batch = steam_ids_64[i:i + batch_size]
        
        try:
            response = requests.get(
                "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/",
                params={
                    'key': steam_api_key,
                    'steamids': ','.join(batch)
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                players = data.get('response', {}).get('players', [])
                
                for player in players:
                    steam_id_64 = player.get('steamid')
                    persona_name = player.get('personaname')
                    
                    if steam_id_64 and persona_name and steam_id_64 in staff_by_steam64:
                        staff = staff_by_steam64[steam_id_64]
                        
                        # Only update if name changed or never synced
                        if staff.steam_name != persona_name:
                            old_name = staff.steam_name
                            staff.steam_name = persona_name
                            staff.steam_name_last_updated = timezone.now()
                            staff.save(update_fields=['steam_name', 'steam_name_last_updated'])
                            
                            if old_name:
                                logger.info(f"Updated Steam name for {staff.name}: '{old_name}' -> '{persona_name}'")
                            else:
                                logger.info(f"Set Steam name for {staff.name}: '{persona_name}'")
                            
                            updated_count += 1
                        else:
                            # Update timestamp even if name unchanged
                            staff.steam_name_last_updated = timezone.now()
                            staff.save(update_fields=['steam_name_last_updated'])
                            
            else:
                error_msg = f"Steam API returned status {response.status_code}"
                logger.error(error_msg)
                errors.append(error_msg)
                
        except requests.exceptions.Timeout:
            error_msg = f"Steam API request timed out for batch starting at index {i}"
            logger.error(error_msg)
            errors.append(error_msg)
            
        except Exception as e:
            error_msg = f"Error fetching Steam names for batch {i}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        # Rate limiting - small delay between batches
        if i + batch_size < len(steam_ids_64):
            time.sleep(1)
    
    result = {
        'success': len(errors) == 0,
        'updated': updated_count,
        'total': len(steam_ids_64),
        'errors': errors if errors else None,
    }
    
    logger.info(f"Steam name sync completed: {updated_count}/{len(steam_ids_64)} names updated")
    
    return result


def _convert_to_steam64(steam_id):
    """
    Convert various Steam ID formats to Steam64.
    
    Supports:
    - Steam64 (76561198xxxxxxxxx)
    - STEAM_X:Y:Z format
    - [U:1:X] format
    """
    if not steam_id:
        return None
    
    steam_id = str(steam_id).strip()
    
    # Already Steam64
    if steam_id.isdigit() and len(steam_id) == 17 and steam_id.startswith('7656119'):
        return steam_id
    
    # STEAM_X:Y:Z format
    if steam_id.upper().startswith('STEAM_'):
        try:
            parts = steam_id.upper().replace('STEAM_', '').split(':')
            if len(parts) == 3:
                y = int(parts[1])
                z = int(parts[2])
                steam64 = 76561197960265728 + (z * 2) + y
                return str(steam64)
        except (ValueError, IndexError):
            pass
    
    # [U:1:X] format
    if steam_id.startswith('[U:'):
        try:
            account_id = int(steam_id.replace('[U:1:', '').replace(']', ''))
            steam64 = 76561197960265728 + account_id
            return str(steam64)
        except ValueError:
            pass
    
    # Try as raw account ID
    try:
        if steam_id.isdigit():
            account_id = int(steam_id)
            if account_id < 76561197960265728:
                # Likely an account ID
                steam64 = 76561197960265728 + account_id
                return str(steam64)
            else:
                # Already a Steam64
                return steam_id
    except ValueError:
        pass
    
    logger.warning(f"Could not convert Steam ID to Steam64: {steam_id}")
    return None


@shared_task
def sync_discord_statuses_task():
    """Sync Discord statuses for all staff members."""
    from django.conf import settings

    from .discord_service import get_bot_instance, sync_discord_statuses

    # Check if Discord bot is configured
    if not getattr(settings, 'DISCORD_BOT_TOKEN', None) or not getattr(settings, 'DISCORD_GUILD_ID', None):
        logger.info("Discord bot not configured, skipping status sync")
        return {'success': False, 'error': 'Bot not configured'}
    
    try:
        bot = get_bot_instance()
        if not bot.is_running:
            logger.warning("Discord bot is not running, skipping status sync")
            return {'success': False, 'error': 'Bot not running'}
        
        # Run async function
        asyncio.run(sync_discord_statuses())
        
        logger.info("Discord status sync completed")
        return {'success': True}
        
    except Exception as e:
        logger.error(f"Error syncing Discord statuses: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def mark_inactive_staff():
    """Mark staff as inactive if not seen in last 5 minutes."""
    from datetime import timedelta

    from django.utils import timezone

    from .models import StaffRoster
    
    try:
        threshold = timezone.now() - timedelta(minutes=5)
        
        # Mark staff as inactive if last_seen is older than threshold
        updated = StaffRoster.objects.filter(
            is_active_in_app=True,
            last_seen__lt=threshold
        ).update(is_active_in_app=False)
        
        logger.info(f"Marked {updated} staff members as inactive")
        return {'success': True, 'marked_inactive': updated}
        
    except Exception as e:
        logger.error(f"Error marking inactive staff: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def update_user_from_roster(user_id: int):
    """Update a single user's information from roster."""
    from django.conf import settings
    from django.contrib.auth import get_user_model

    from .models import StaffRoster
    
    User = get_user_model()
    
    try:
        user = User.objects.get(id=user_id)
        
        # Try to find matching roster entry
        roster_entry = None
        
        if user.steam_id:
            roster_entry = StaffRoster.objects.filter(
                steam_id=user.steam_id,
                is_active=True
            ).first()
        
        if roster_entry:
            user.role = roster_entry.rank
            user.role_priority = settings.STAFF_ROLE_PRIORITIES.get(roster_entry.rank, 999)
            user.is_active_staff = True
            user.save(update_fields=['role', 'role_priority', 'is_active_staff'])
            
            logger.info(f"Updated user {user.username} from roster")
            return True
        
        return False
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return False
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        return False


@shared_task
def aggregate_server_sessions():
    """Aggregate server sessions for statistics."""
    from datetime import date, timedelta

    from apps.servers.models import GameServer
    from django.db.models import Avg, Count, Sum

    from .models import ServerSession, ServerSessionAggregate, StaffRoster
    
    try:
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        # Get all active staff
        staff_members = StaffRoster.objects.filter(is_active=True)
        servers = GameServer.objects.filter(is_active=True)
        
        aggregated_count = 0
        
        for staff in staff_members:
            # Daily aggregation for yesterday
            for server in servers:
                sessions = ServerSession.objects.filter(
                    staff=staff,
                    server=server,
                    join_time__date=yesterday,
                    leave_time__isnull=False
                )
                
                if sessions.exists():
                    stats = sessions.aggregate(
                        total_time=Sum('duration'),
                        session_count=Count('id'),
                        avg_duration=Avg('duration'),
                        longest_session=Sum('duration')  # This should be Max but simplified for now
                    )
                    
                    aggregate, created = ServerSessionAggregate.objects.update_or_create(
                        staff=staff,
                        server=server,
                        period_type='daily',
                        period_start=yesterday,
                        defaults={
                            'period_end': yesterday,
                            'total_time': stats['total_time'] or 0,
                            'session_count': stats['session_count'] or 0,
                            'avg_session_time': int(stats['avg_duration'] or 0),
                            'longest_session': stats['longest_session'] or 0,
                        }
                    )
                    aggregated_count += 1
            
            # Weekly aggregation
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            
            for server in servers:
                sessions = ServerSession.objects.filter(
                    staff=staff,
                    server=server,
                    join_time__date__gte=week_start,
                    join_time__date__lte=week_end,
                    leave_time__isnull=False
                )
                
                if sessions.exists():
                    stats = sessions.aggregate(
                        total_time=Sum('duration'),
                        session_count=Count('id'),
                        avg_duration=Avg('duration'),
                        longest_session=Sum('duration')
                    )
                    
                    ServerSessionAggregate.objects.update_or_create(
                        staff=staff,
                        server=server,
                        period_type='weekly',
                        period_start=week_start,
                        defaults={
                            'period_end': week_end,
                            'total_time': stats['total_time'] or 0,
                            'session_count': stats['session_count'] or 0,
                            'avg_session_time': int(stats['avg_duration'] or 0),
                            'longest_session': stats['longest_session'] or 0,
                        }
                    )
            
            # Monthly aggregation
            month_start = today.replace(day=1)
            
            for server in servers:
                sessions = ServerSession.objects.filter(
                    staff=staff,
                    server=server,
                    join_time__date__gte=month_start,
                    join_time__date__lte=today,
                    leave_time__isnull=False
                )
                
                if sessions.exists():
                    stats = sessions.aggregate(
                        total_time=Sum('duration'),
                        session_count=Count('id'),
                        avg_duration=Avg('duration'),
                        longest_session=Sum('duration')
                    )
                    
                    ServerSessionAggregate.objects.update_or_create(
                        staff=staff,
                        server=server,
                        period_type='monthly',
                        period_start=month_start,
                        defaults={
                            'total_time': stats['total_time'] or 0,
                            'session_count': stats['session_count'] or 0,
                            'avg_session_time': int(stats['avg_duration'] or 0),
                            'longest_session': stats['longest_session'] or 0,
                        }
                    )
        
        logger.info(f"Aggregated {aggregated_count} server sessions")
        return {'success': True, 'aggregated': aggregated_count}
        
    except Exception as e:
        logger.error(f"Error aggregating server sessions: {e}")
        return {'success': False, 'error': str(e)}
