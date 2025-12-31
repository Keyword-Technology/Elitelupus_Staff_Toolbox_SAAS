import csv
import logging
from io import StringIO

import requests
from apps.system_settings.models import SystemSetting
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Staff, StaffHistoryEvent, StaffRoster, StaffSyncLog

logger = logging.getLogger(__name__)
User = get_user_model()


class StaffSyncService:
    """Service for syncing staff data from Google Sheets."""
    
    SHEET_NAME = "Staff Roster"  # Changed from "Roster" to "Staff Roster"
    SHEET_GID = "160655123"  # Alternative: can use GID instead
    
    @property
    def sheet_id(self):
        """Get Google Sheets ID with database override support."""
        # Try to get from system settings first, fallback to environment variable
        sheet_id = SystemSetting.get_setting_value('GOOGLE_SHEETS_ID', settings.GOOGLE_SHEETS_ID)
        logger.info(f"Using Google Sheets ID: {sheet_id}")
        return sheet_id
    
    @property
    def sheet_url(self):
        # Using gid to specifically target the Staff Roster sheet tab
        return f"https://docs.google.com/spreadsheets/d/{self.sheet_id}/gviz/tq?tqx=out:csv&gid={self.SHEET_GID}"
    
    def fetch_sheet_data(self):
        """Fetch data from Google Sheets as CSV."""
        try:
            response = requests.get(self.sheet_url, timeout=30)
            response.raise_for_status()
            return response.content.decode('utf-8')
        except requests.RequestException as e:
            logger.error(f"Error fetching Google Sheet: {e}")
            raise
    
    def parse_csv_data(self, csv_content):
        """Parse CSV content into list of dictionaries.
        
        The Google Sheet exports with a quirky format:
        - Row 0 has headers merged with first data row: "Rank Manager", "Timezone GMT", etc.
        - Row 1+ has just values: "Manager", "GMT", etc.
        - Each row can have TWO staff members (columns 2-8 and 11-17)
        """
        staff_list = []
        reader = csv.reader(StringIO(csv_content))
        rows = list(reader)
        
        if not rows:
            logger.error("No data found in CSV")
            return staff_list
        
        # Fixed column positions based on sheet structure:
        # Only use Set 1: columns 2-8 (Rank, Timezone, Time, Name, SteamID, DiscordID, Discord Tag)
        # Set 2 (columns 11+) contains stale/duplicate data - ignore it
        COLUMN_SETS = [
            {'rank': 2, 'timezone': 3, 'time': 4, 'name': 5, 'steam': 6, 'discord_id': 7, 'discord_tag': 8},
        ]
        
        # Helper to strip prefix from merged header+value cells (e.g., "Rank Manager" -> "Manager")
        def strip_prefix(value, prefix):
            """Strip prefix from value if present (case-insensitive)."""
            if not value:
                return ''
            value = value.strip().replace('"', '')
            if value.lower().startswith(prefix.lower() + ' '):
                return value[len(prefix) + 1:].strip()
            return value
        
        for row_num, row in enumerate(rows):
            if not row or len(row) < 7:
                continue
            
            # Process both column sets (two staff members per row potentially)
            for col_set in COLUMN_SETS:
                if len(row) <= col_set['rank']:
                    continue
                
                try:
                    # Get raw values
                    raw_rank = row[col_set['rank']] if len(row) > col_set['rank'] else ''
                    raw_timezone = row[col_set['timezone']] if len(row) > col_set['timezone'] else ''
                    raw_time = row[col_set['time']] if col_set['time'] is not None and len(row) > col_set['time'] else ''
                    raw_name = row[col_set['name']] if len(row) > col_set['name'] else ''
                    raw_steam = row[col_set['steam']] if len(row) > col_set['steam'] else ''
                    raw_discord_id = row[col_set['discord_id']] if len(row) > col_set['discord_id'] else ''
                    raw_discord_tag = row[col_set['discord_tag']] if len(row) > col_set['discord_tag'] else ''
                    
                    # For row 0, strip the header prefix; for other rows, use as-is
                    if row_num == 0:
                        rank = strip_prefix(raw_rank, 'Rank')
                        timezone = strip_prefix(raw_timezone, 'Timezone')
                        active_time = strip_prefix(raw_time, 'Time')
                        name = strip_prefix(raw_name, 'Name')
                        steam_id = strip_prefix(raw_steam, 'SteamID')
                        discord_id = strip_prefix(raw_discord_id, 'DiscordID')
                        discord_tag = strip_prefix(raw_discord_tag, 'Discord Tag')
                    else:
                        rank = raw_rank.strip().replace('"', '')
                        timezone = raw_timezone.strip().replace('"', '')
                        active_time = raw_time.strip().replace('"', '')
                        name = raw_name.strip().replace('"', '')
                        steam_id = raw_steam.strip().replace('"', '')
                        discord_id = raw_discord_id.strip().replace('"', '')
                        discord_tag = raw_discord_tag.strip().replace('"', '')
                    
                    # Skip empty entries or header-only entries
                    if not rank or not name:
                        continue
                    if rank.lower() in ['rank', 'staff rank', 'role']:
                        continue
                    
                    # Parse steam ID
                    parsed_steam_id = self._parse_steam_id(steam_id) if steam_id else None
                    
                    staff_data = {
                        'rank': rank,
                        'timezone': timezone,
                        'active_time': active_time,
                        'name': name,
                        'steam_id': parsed_steam_id,
                        'discord_id': discord_id if discord_id else None,
                        'discord_tag': discord_tag if discord_tag else None,
                    }
                    
                    # Only add if we have at least a name and one identifier
                    if staff_data['name'] and (staff_data['steam_id'] or staff_data['discord_id']):
                        staff_list.append(staff_data)
                        logger.debug(f"Parsed staff member: {staff_data['name']} ({staff_data['rank']})")
                    
                except (IndexError, ValueError) as e:
                    logger.warning(f"Error parsing row {row_num}, column set {col_set}: {e}")
                    continue
        
        # Deduplicate by steam_id (keep first occurrence)
        seen_steam_ids = set()
        unique_staff = []
        for staff in staff_list:
            steam_id = staff.get('steam_id')
            if steam_id and steam_id in seen_steam_ids:
                logger.debug(f"Skipping duplicate: {staff['name']} ({steam_id})")
                continue
            if steam_id:
                seen_steam_ids.add(steam_id)
            unique_staff.append(staff)
        
        logger.info(f"Parsed {len(unique_staff)} unique staff members from CSV (removed {len(staff_list) - len(unique_staff)} duplicates)")
        return unique_staff
    
    def _parse_steam_id(self, steam_id_raw):
        """Parse and clean Steam ID."""
        if not steam_id_raw:
            return None
        
        steam_id = steam_id_raw.strip().replace('"', '')
        
        # Handle different Steam ID formats
        if steam_id.startswith('STEAM_'):
            return steam_id
        elif steam_id.startswith('7656119'):
            # Convert SteamID64 to SteamID
            return self._convert_steam_id_64(steam_id)
        
        return steam_id if steam_id else None
    
    def _convert_steam_id_64(self, steam_id_64):
        """Convert SteamID64 to SteamID format."""
        try:
            steam_id_64 = int(steam_id_64)
            y = steam_id_64 & 1
            z = (steam_id_64 - 76561197960265728) // 2
            return f"STEAM_0:{y}:{z}"
        except (ValueError, TypeError):
            return None
    
    def sync_staff_roster(self):
        """Main sync method - fetches and updates staff roster."""
        log = StaffSyncLog()
        
        try:
            # Fetch data
            csv_content = self.fetch_sheet_data()
            staff_data = self.parse_csv_data(csv_content)
            
            log.records_synced = len(staff_data)
            
            # Track existing records by unique identifiers
            existing_identifiers = set()
            for entry in StaffRoster.objects.all():
                identifier = self._get_unique_identifier(entry.staff.steam_id, entry.staff.discord_id, entry.staff.name)
                existing_identifiers.add(identifier)
            
            processed_identifiers = set()
            
            for data in staff_data:
                steam_id = data.get('steam_id')
                discord_id = data.get('discord_id')
                name = data.get('name')
                
                # Skip if no identifiable information
                if not steam_id and not discord_id and not name:
                    logger.warning(f"Skipping entry with no identifiable information: {data}")
                    continue
                
                identifier = self._get_unique_identifier(steam_id, discord_id, name)
                processed_identifiers.add(identifier)
                
                # Find or create Staff record first (by steam_id as primary key)
                if not steam_id:
                    logger.warning(f"Skipping staff member without Steam ID: {name}")
                    continue
                
                staff, staff_created = Staff.objects.get_or_create(
                    steam_id=steam_id,
                    defaults={
                        'name': name,
                        'discord_id': discord_id,
                        'discord_tag': data['discord_tag'],
                        'staff_status': 'active',
                        'current_role': data['rank'],
                        'current_role_priority': settings.STAFF_ROLE_PRIORITIES.get(data['rank'], 999),
                        'staff_since': timezone.now(),
                    }
                )
                
                if not staff_created:
                    # Update existing Staff record
                    staff.name = name
                    staff.discord_id = discord_id
                    staff.discord_tag = data['discord_tag']
                    staff.current_role = data['rank']
                    staff.current_role_priority = settings.STAFF_ROLE_PRIORITIES.get(data['rank'], 999)
                    staff.staff_status = 'active'
                    staff.last_seen = timezone.now()
                    staff.save()
                    staff.last_seen = timezone.now()
                    staff.save()
                
                # Now find or create StaffRoster entry
                roster_entry = StaffRoster.objects.filter(staff=staff).first()
                
                # Update or create the roster entry
                if roster_entry:
                    # Track if rank changed
                    old_rank = roster_entry.rank
                    old_rank_priority = roster_entry.rank_priority
                    new_rank = data['rank']
                    new_rank_priority = settings.STAFF_ROLE_PRIORITIES.get(data['rank'], 999)
                    
                    # Check if this staff was previously inactive (rejoining)
                    was_inactive = not roster_entry.is_active
                    
                    # Update existing entry
                    roster_entry.rank = new_rank
                    roster_entry.rank_priority = new_rank_priority
                    roster_entry.timezone = data['timezone']
                    roster_entry.active_time = data['active_time']
                    roster_entry.is_active = True
                    roster_entry.save()
                    log.records_updated += 1
                    
                    # Track history events
                    if was_inactive:
                        # Staff member rejoined
                        StaffHistoryEvent.objects.create(
                            staff=staff,
                            event_type='rejoined',
                            new_rank=new_rank,
                            new_rank_priority=new_rank_priority,
                            event_date=timezone.now(),
                            auto_detected=True
                        )
                    elif old_rank != new_rank:
                        # Rank changed - determine if promotion or demotion
                        if new_rank_priority < old_rank_priority:
                            event_type = 'promoted'
                        elif new_rank_priority > old_rank_priority:
                            event_type = 'demoted'
                        else:
                            event_type = 'role_change'
                        
                        StaffHistoryEvent.objects.create(
                            staff=staff,
                            event_type=event_type,
                            old_rank=old_rank,
                            new_rank=new_rank,
                            old_rank_priority=old_rank_priority,
                            new_rank_priority=new_rank_priority,
                            event_date=timezone.now(),
                            auto_detected=True
                        )
                else:
                    # Create new roster entry
                    roster_entry = StaffRoster.objects.create(
                        staff=staff,
                        rank=data['rank'],
                        rank_priority=settings.STAFF_ROLE_PRIORITIES.get(data['rank'], 999),
                        timezone=data['timezone'],
                        active_time=data['active_time'],
                        is_active=True,
                    )
                    log.records_added += 1
                    
                    # Track join event
                    StaffHistoryEvent.objects.create(
                        staff=staff,
                        event_type='joined',
                        new_rank=data['rank'],
                        new_rank_priority=settings.STAFF_ROLE_PRIORITIES.get(data['rank'], 999),
                        event_date=timezone.now(),
                        auto_detected=True
                    )
                
                # Link to user account if exists
                self._link_to_user(staff)
            
            # Handle removed staff - mark roster entry as inactive (preserving all data)
            removed_identifiers = existing_identifiers - processed_identifiers
            if removed_identifiers:
                # This is approximate - we need to find entries that weren't processed
                for entry in StaffRoster.objects.filter(is_active=True):
                    identifier = self._get_unique_identifier(entry.staff.steam_id, entry.staff.discord_id, entry.staff.name)
                    if identifier in removed_identifiers:
                        old_rank = entry.rank
                        old_rank_priority = entry.rank_priority
                        
                        # Mark roster entry as inactive (preserves all data and history)
                        entry.is_active = False
                        entry.save()
                        log.records_removed += 1
                        
                        # Update Staff status
                        entry.staff.staff_status = 'inactive'
                        entry.staff.staff_left_at = timezone.now()
                        entry.staff.save(update_fields=['staff_status', 'staff_left_at'])
                        
                        # Update linked user account if exists
                        if entry.staff.user:
                            entry.staff.user.is_active_staff = False
                            entry.staff.user.is_legacy_staff = True
                            entry.staff.user.staff_left_at = timezone.now()
                            entry.staff.user.save(update_fields=['is_active_staff', 'is_legacy_staff', 'staff_left_at'])
                        
                        # Track removal event
                        StaffHistoryEvent.objects.create(
                            staff=entry.staff,
                            event_type='removed',
                            old_rank=old_rank,
                            old_rank_priority=old_rank_priority,
                            event_date=timezone.now(),
                            auto_detected=True
                        )
            
            log.success = True
            log.save()
            
            logger.info(f"Staff sync completed: {log.records_synced} synced, "
                       f"{log.records_added} added, {log.records_updated} updated, "
                       f"{log.records_removed} removed")
            
            # Sync user access based on roster
            try:
                access_result = self.sync_user_access()
                logger.info(f"User access sync: {access_result['activated']} activated, "
                           f"{access_result['deactivated']} deactivated")
            except Exception as e:
                logger.error(f"Error syncing user access: {e}")
            
            return log
            
        except Exception as e:
            log.success = False
            log.error_message = str(e)
            log.save()
            logger.error(f"Staff sync failed: {e}")
            raise
    
    def _get_unique_identifier(self, steam_id, discord_id, name):
        """Generate a unique identifier for a staff member."""
        # Prefer steam_id, then discord_id, then name
        if steam_id:
            return f"steam:{steam_id}"
        elif discord_id:
            return f"discord:{discord_id}"
        else:
            return f"name:{name}"
    
    def _link_to_user(self, staff):
        """Link staff to user account if exists."""
        user = None
        
        # Try to find by Steam ID first
        if staff.steam_id:
            user = User.objects.filter(steam_id=staff.steam_id).first()
        
        # Try Discord ID if no Steam match
        if not user and staff.discord_id:
            user = User.objects.filter(discord_id=staff.discord_id).first()
        
        if user:
            staff.user = user
            staff.save(update_fields=['user'])
            
            # Check if user is returning from legacy staff
            if user.is_legacy_staff:
                # Re-added to staff roster - promote to SYSADMIN
                user.role = 'SYSADMIN'
                user.role_priority = 0
                user.is_active_staff = True
                user.is_legacy_staff = False
                user.staff_left_at = None
                user.save(update_fields=['role', 'role_priority', 'is_active_staff', 'is_legacy_staff', 'staff_left_at'])
                logger.info(f"Re-added legacy staff {user.username} as SYSADMIN")
            else:
                # Update user role to match roster
                user.role = staff.current_role
                user.role_priority = staff.current_role_priority
                user.is_active_staff = True
                user.save(update_fields=['role', 'role_priority', 'is_active_staff'])
    
    def get_staff_member_data(self, steam_id=None, discord_id=None):
        """Get staff member data by Steam ID or Discord ID."""
        try:
            if steam_id:
                staff = Staff.objects.filter(steam_id=steam_id).first()
                if staff:
                    roster = StaffRoster.objects.filter(staff=staff, is_active=True).first()
                    if roster:
                        return {
                            'rank': roster.rank,
                            'name': staff.name,
                            'timezone': roster.timezone,
                            'discord_id': staff.discord_id,
                        }
            
            if discord_id:
                staff = Staff.objects.filter(discord_id=discord_id).first()
                if staff:
                    roster = StaffRoster.objects.filter(staff=staff, is_active=True).first()
                    if roster:
                        return {
                            'rank': roster.rank,
                            'name': staff.name,
                            'timezone': roster.timezone,
                            'steam_id': staff.steam_id,
                        }
            
            return None
        except Exception as e:
            logger.error(f"Error getting staff member data: {e}")
            return None
    
    def get_all_staff(self):
        """Get all active staff members."""
        return list(StaffRoster.objects.filter(is_active=True).select_related('staff').values(
            'staff__steam_id', 'staff__name', 'staff__discord_id', 'staff__discord_tag',
            'rank', 'timezone', 'active_time'
        ))
    
    def sync_user_access(self):
        """Sync user account active status based on staff roster.
        Move users not in roster to legacy staff (except SYSADMIN).
        Activates users in roster (including legacy staff returning).
        """
        deactivated_count = 0
        activated_count = 0
        
        # Get all active roster entries with identifiers
        active_roster = StaffRoster.objects.filter(is_active=True).select_related('staff')
        active_steam_ids = set(r.staff.steam_id for r in active_roster if r.staff.steam_id)
        active_discord_ids = set(r.staff.discord_id for r in active_roster if r.staff.discord_id)
        
        # Process all users (except SYSADMIN - they're always allowed)
        for user in User.objects.exclude(role='SYSADMIN'):
            # Check if user is in active roster by Steam ID or Discord ID
            in_roster = False
            if user.steam_id and user.steam_id in active_steam_ids:
                in_roster = True
            elif user.discord_id and user.discord_id in active_discord_ids:
                in_roster = True
            
            # Update user active status
            if in_roster and not user.is_active:
                user.is_active = True
                user.is_active_staff = True
                user.save(update_fields=['is_active', 'is_active_staff'])
                activated_count += 1
                logger.info(f"Activated user: {user.username}")
            elif not in_roster and user.is_active and user.is_active_staff:
                # Mark as legacy staff (handled by removal logic in sync)
                # This catches any users that weren't properly handled
                user.is_active = True  # Keep account active
                user.is_active_staff = False
                user.is_legacy_staff = True
                user.staff_left_at = timezone.now()
                user.save(update_fields=['is_active', 'is_active_staff', 'is_legacy_staff', 'staff_left_at'])
                deactivated_count += 1
                logger.info(f"Moved user to legacy staff: {user.username} (not in staff roster)")
        
        logger.info(f"User access sync completed: {activated_count} activated, {deactivated_count} deactivated")
        return {'activated': activated_count, 'deactivated': deactivated_count}
    
    def is_user_in_roster(self, user):
        """Check if a user is in the active staff roster.
        SYSADMIN accounts are always allowed.
        """
        if user.role == 'SYSADMIN':
            return True
        
        # Check by Steam ID
        if user.steam_id:
            if StaffRoster.objects.filter(staff__steam_id=user.steam_id, is_active=True).exists():
                return True
        
        # Check by Discord ID
        if user.discord_id:
            if StaffRoster.objects.filter(staff__discord_id=user.discord_id, is_active=True).exists():
                return True
        
        return False
