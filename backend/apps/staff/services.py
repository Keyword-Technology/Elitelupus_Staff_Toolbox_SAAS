import requests
import csv
from io import StringIO
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
import logging

from .models import StaffRoster, StaffSyncLog

logger = logging.getLogger(__name__)
User = get_user_model()


class StaffSyncService:
    """Service for syncing staff data from Google Sheets."""
    
    SHEET_ID = settings.GOOGLE_SHEETS_ID
    SHEET_NAME = "Roster"
    
    @property
    def sheet_url(self):
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
        
        # Expected columns based on the screenshot:
        # Rank, Timezone, Time, Name, SteamID, DiscordID, Discord Tag
        for row in reader:
            if len(row) >= 7 and row[0].strip():  # Has at least required fields and rank
                try:
                    staff_data = {
                        'rank': row[0].strip().replace('"', ''),
                        'timezone': row[1].strip().replace('"', '') if len(row) > 1 else '',
                        'active_time': row[2].strip().replace('"', '') if len(row) > 2 else '',
                        'name': row[3].strip().replace('"', '') if len(row) > 3 else '',
                        'steam_id': self._parse_steam_id(row[4]) if len(row) > 4 else None,
                        'discord_id': row[5].strip().replace('"', '') if len(row) > 5 else None,
                        'discord_tag': row[6].strip().replace('"', '') if len(row) > 6 else None,
                    }
                    
                    # Skip header rows or invalid data
                    if staff_data['rank'].lower() not in ['rank', '']:
                        staff_list.append(staff_data)
                except (IndexError, ValueError) as e:
                    logger.warning(f"Error parsing row: {row}, error: {e}")
                    continue
        
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
            
            # Track existing records
            existing_steam_ids = set(
                StaffRoster.objects.values_list('steam_id', flat=True)
            )
            processed_steam_ids = set()
            
            for data in staff_data:
                steam_id = data.get('steam_id')
                if not steam_id:
                    continue
                
                processed_steam_ids.add(steam_id)
                
                # Try to find existing record
                roster_entry, created = StaffRoster.objects.update_or_create(
                    steam_id=steam_id,
                    defaults={
                        'rank': data['rank'],
                        'timezone': data['timezone'],
                        'active_time': data['active_time'],
                        'name': data['name'],
                        'discord_id': data['discord_id'],
                        'discord_tag': data['discord_tag'],
                        'is_active': True,
                    }
                )
                
                if created:
                    log.records_added += 1
                else:
                    log.records_updated += 1
                
                # Link to user account if exists
                self._link_to_user(roster_entry)
            
            # Mark removed staff as inactive
            removed_ids = existing_steam_ids - processed_steam_ids
            if removed_ids:
                StaffRoster.objects.filter(steam_id__in=removed_ids).update(is_active=False)
                log.records_removed = len(removed_ids)
            
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
