import csv
import logging
from io import StringIO

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import StaffRoster, StaffSyncLog

logger = logging.getLogger(__name__)
User = get_user_model()


class StaffSyncService:
    """Service for syncing staff data from Google Sheets."""
    
    SHEET_ID = settings.GOOGLE_SHEETS_ID
    SHEET_NAME = "Staff Roster"  # Changed from "Roster" to "Staff Roster"
    SHEET_GID = "160655123"  # Alternative: can use GID instead
    
    @property
    def sheet_url(self):
        # Using sheet name - can also use gid={self.SHEET_GID} instead of sheet={self.SHEET_NAME}
        return f"https://docs.google.com/spreadsheets/d/{self.SHEET_ID}/gviz/tq?tqx=out:csv&sheet={self.SHEET_NAME}"
    
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
        """Parse CSV content into list of dictionaries."""
        staff_list = []
        reader = csv.reader(StringIO(csv_content))
        
        # Skip header row
        headers = next(reader, None)
        if not headers:
            return staff_list
        
        # Expected columns from "Staff Roster" Google Sheet:
        # Column 0: Empty, Column 1: Number (99), Column 2: Rank, Column 3: Timezone, 
        # Column 4: Time, Column 5: Name, Column 6: SteamID, Column 7: DiscordID, Column 8: Discord Tag
        for row in reader:
            # Check if row has enough columns and has a valid rank (column 2)
            if len(row) >= 9 and len(row) > 2 and row[2].strip():
                try:
                    rank = row[2].strip().replace('"', '')
                    
                    # Skip header rows or invalid data
                    if rank.lower() in ['rank', 'staff rank', 'rank manager', '']:
                        continue
                    
                    staff_data = {
                        'rank': rank,
                        'timezone': row[3].strip().replace('"', '').replace('Timezone ', '') if len(row) > 3 else '',
                        'active_time': row[4].strip().replace('"', '').replace('Time ', '') if len(row) > 4 else '',
                        'name': row[5].strip().replace('"', '').replace('Name ', '') if len(row) > 5 else '',
                        'steam_id': self._parse_steam_id(row[6].replace('SteamID ', '').strip()) if len(row) > 6 else None,
                        'discord_id': row[7].strip().replace('"', '').replace('DiscordID ', '') if len(row) > 7 else None,
                        'discord_tag': row[8].strip().replace('"', '').replace('Discord Tag ', '') if len(row) > 8 else None,
                    }
                    
                    # Only add if we have at least a name and one identifier
                    if staff_data['name'] and (staff_data['steam_id'] or staff_data['discord_id']):
                        staff_list.append(staff_data)
                        logger.debug(f"Parsed staff member: {staff_data['name']} ({staff_data['rank']})")
                except (IndexError, ValueError) as e:
                    logger.warning(f"Error parsing row: {row}, error: {e}")
                    continue
        
        logger.info(f"Parsed {len(staff_list)} staff members from CSV")
        return staff_list
    
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
                identifier = self._get_unique_identifier(entry.steam_id, entry.discord_id, entry.name)
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
                
                # Try to find existing record by steam_id first, then discord_id, then name
                roster_entry = None
                if steam_id:
                    roster_entry = StaffRoster.objects.filter(steam_id=steam_id).first()
                
                if not roster_entry and discord_id:
                    roster_entry = StaffRoster.objects.filter(discord_id=discord_id).first()
                
                if not roster_entry and name:
                    roster_entry = StaffRoster.objects.filter(name=name).first()
                
                # Update or create the roster entry
                if roster_entry:
                    # Update existing entry
                    roster_entry.rank = data['rank']
                    roster_entry.timezone = data['timezone']
                    roster_entry.active_time = data['active_time']
                    roster_entry.name = data['name']
                    roster_entry.steam_id = steam_id
                    roster_entry.discord_id = discord_id
                    roster_entry.discord_tag = data['discord_tag']
                    roster_entry.is_active = True
                    roster_entry.save()
                    log.records_updated += 1
                else:
                    # Create new entry
                    roster_entry = StaffRoster.objects.create(
                        rank=data['rank'],
                        timezone=data['timezone'],
                        active_time=data['active_time'],
                        name=data['name'],
                        steam_id=steam_id,
                        discord_id=discord_id,
                        discord_tag=data['discord_tag'],
                        is_active=True,
                    )
                    log.records_added += 1
                
                # Link to user account if exists
                self._link_to_user(roster_entry)
            
            # Mark removed staff as inactive
            removed_identifiers = existing_identifiers - processed_identifiers
            if removed_identifiers:
                # This is approximate - we need to find entries that weren't processed
                for entry in StaffRoster.objects.filter(is_active=True):
                    identifier = self._get_unique_identifier(entry.steam_id, entry.discord_id, entry.name)
                    if identifier in removed_identifiers:
                        entry.is_active = False
                        entry.save()
                        log.records_removed += 1
            
            log.success = True
            log.save()
            
            logger.info(f"Staff sync completed: {log.records_synced} synced, "
                       f"{log.records_added} added, {log.records_updated} updated, "
                       f"{log.records_removed} removed")
            
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
    
    def _link_to_user(self, roster_entry):
        """Link roster entry to user account if exists."""
        user = None
        
        # Try to find by Steam ID first
        if roster_entry.steam_id:
            user = User.objects.filter(steam_id=roster_entry.steam_id).first()
        
        # Try Discord ID if no Steam match
        if not user and roster_entry.discord_id:
            user = User.objects.filter(discord_id=roster_entry.discord_id).first()
        
        if user:
            roster_entry.user = user
            roster_entry.save(update_fields=['user'])
            
            # Update user role if needed
            if user.role != roster_entry.rank:
                user.role = roster_entry.rank
                user.role_priority = settings.STAFF_ROLE_PRIORITIES.get(roster_entry.rank, 999)
                user.is_active_staff = True
                user.save(update_fields=['role', 'role_priority', 'is_active_staff'])
    
    def get_staff_member_data(self, steam_id=None, discord_id=None):
        """Get staff member data by Steam ID or Discord ID."""
        try:
            if steam_id:
                roster = StaffRoster.objects.filter(steam_id=steam_id, is_active=True).first()
                if roster:
                    return {
                        'rank': roster.rank,
                        'name': roster.name,
                        'timezone': roster.timezone,
                        'discord_id': roster.discord_id,
                    }
            
            if discord_id:
                roster = StaffRoster.objects.filter(discord_id=discord_id, is_active=True).first()
                if roster:
                    return {
                        'rank': roster.rank,
                        'name': roster.name,
                        'timezone': roster.timezone,
                        'steam_id': roster.steam_id,
                    }
            
            return None
        except Exception as e:
            logger.error(f"Error getting staff member data: {e}")
            return None
    
    def get_all_staff(self):
        """Get all active staff members."""
        return list(StaffRoster.objects.filter(is_active=True).values())
