"""Steam profile lookup and tracking service."""
from datetime import datetime

import requests
from django.conf import settings
from django.utils import timezone

from .models import SteamProfileHistory, SteamProfileSearch
from .steamid_io_scraper import scrape_steamid_io
from .steamid_scraper import scrape_steamid_profile


class SteamLookupService:
    """Service for looking up and tracking Steam profiles."""
    
    def __init__(self):
        self.steam_api_key = getattr(settings, 'SOCIAL_AUTH_STEAM_API_KEY', None)
    
    def lookup_profile(self, steam_id, user=None):
        """
        Look up a Steam profile and track the search.
        
        Args:
            steam_id: Steam ID (any format)
            user: User performing the search
            
        Returns:
            dict: Enhanced profile data with search history
        """
        # Convert to Steam ID 64
        steam_id_64 = self._convert_to_steam_id_64(steam_id)
        steam_id_converted = self._convert_to_steam_id(steam_id_64)
        
        # Get or create search record
        search_record, created = SteamProfileSearch.objects.get_or_create(
            steam_id_64=steam_id_64,
            defaults={'steam_id': steam_id_converted}
        )
        
        # Ensure past_names is initialized (for records created before migration)
        if search_record.past_names is None:
            search_record.past_names = []
        
        # Store previous data for change detection
        previous_data = {
            'persona_name': search_record.persona_name,
            'vac_bans': search_record.vac_bans,
            'game_bans': search_record.game_bans,
            'days_since_last_ban': search_record.days_since_last_ban,
            'profile_state': search_record.profile_state,
        }
        
        # Fetch fresh data from multiple sources
        profile_data = self._fetch_steam_api_data(steam_id_64)
        ban_data = self._fetch_ban_data(steam_id_64)
        
        # Fetch enhanced data from steamid.pro scraper
        scraped_data = self._fetch_scraped_data(steam_id_64)
        
        # Update search record
        search_record.steam_id = steam_id_converted
        search_record.search_count += 1 if not created else 0
        search_record.last_searched_at = timezone.now()
        search_record.last_searched_by = user
        
        # Update profile data
        if profile_data:
            new_name = profile_data.get('personaname', '')
            old_name = search_record.persona_name
            
            # Track name changes in past_names
            if new_name and new_name != old_name:
                self._add_to_past_names(search_record, new_name)
            
            search_record.persona_name = new_name
            search_record.profile_url = profile_data.get('profileurl', '')
            search_record.avatar_url = profile_data.get('avatarfull', '')
            print(f"Setting avatar_url to: {search_record.avatar_url}")
            search_record.profile_state = self._get_profile_state(profile_data)
            search_record.real_name = profile_data.get('realname', '')
            search_record.location = profile_data.get('loccountrycode', '')
            search_record.is_private = profile_data.get('communityvisibilitystate', 1) != 3
            search_record.is_limited = profile_data.get('islimitedaccount', False)
            
            # Additional Steam profile fields
            search_record.steam_id_3 = self._convert_to_steam_id_3(steam_id_64)
            search_record.custom_url = profile_data.get('profileurl', '').split('/')[-2] if profile_data.get('profileurl') else ''
            search_record.persona_state = profile_data.get('personastate', 0)
            search_record.persona_state_flags = profile_data.get('personastateflags', 0)
            search_record.comment_permission = profile_data.get('commentpermission', False)
            
            # Last logoff
            if 'lastlogoff' in profile_data:
                search_record.last_logoff = datetime.fromtimestamp(
                    profile_data['lastlogoff'],
                    tz=timezone.utc
                )
            
            # Game info (if currently playing)
            search_record.game_id = profile_data.get('gameid', '')
            search_record.game_server_ip = profile_data.get('gameserverip', '')
            search_record.game_extra_info = profile_data.get('gameextrainfo', '')
            
            # Location info
            search_record.country_code = profile_data.get('loccountrycode', '')
            search_record.state_code = profile_data.get('locstatecode', '')
            search_record.city_id = profile_data.get('loccityid', None)
            
            # Account creation date
            if 'timecreated' in profile_data:
                search_record.account_created = datetime.fromtimestamp(
                    profile_data['timecreated'], 
                    tz=timezone.utc
                )
        
        # Update ban data
        if ban_data:
            search_record.vac_bans = ban_data.get('NumberOfVACBans', 0)
            search_record.game_bans = ban_data.get('NumberOfGameBans', 0)
            search_record.days_since_last_ban = ban_data.get('DaysSinceLastBan', None)
            search_record.community_banned = ban_data.get('CommunityBanned', False)
            # Trade ban: empty string or 'none' means no ban
            trade_ban_value = ban_data.get('EconomyBan', 'none')
            search_record.trade_ban = trade_ban_value if trade_ban_value else 'none'
        
        # Update scraped data from steamid.pro and steamid.io (only fill missing fields)
        if scraped_data:
            # Use scraped avatar ONLY if Steam API didn't provide one
            if not search_record.avatar_url and scraped_data.get('avatar_url'):
                search_record.avatar_url = scraped_data['avatar_url']
            
            # Use scraped display name ONLY if Steam API didn't provide one
            if not search_record.persona_name and scraped_data.get('display_name'):
                search_record.persona_name = scraped_data['display_name']
            
            # Use scraped profile state ONLY if Steam API didn't provide one
            if not search_record.profile_state and scraped_data.get('profile_state'):
                search_record.profile_state = scraped_data['profile_state']
            
            # Enhanced steamid.io and steamid.pro fields - always store these
            if scraped_data.get('account_name'):
                search_record.account_name = scraped_data['account_name']
            if scraped_data.get('vanity_url'):
                search_record.vanity_url = scraped_data['vanity_url']
            if scraped_data.get('account_id'):
                search_record.account_id = scraped_data['account_id']
            if scraped_data.get('steam_id_2'):
                search_record.steam_id_2 = scraped_data['steam_id_2']
            if scraped_data.get('invite_url'):
                search_record.invite_url = scraped_data['invite_url']
            if scraped_data.get('invite_url_short'):
                search_record.invite_url_short = scraped_data['invite_url_short']
            if scraped_data.get('fivem_hex'):
                search_record.fivem_hex = scraped_data['fivem_hex']
            if scraped_data.get('online_status'):
                search_record.online_status = scraped_data['online_status']
            if scraped_data.get('estimated_value'):
                search_record.estimated_value = scraped_data['estimated_value']
            if scraped_data.get('rating_value') is not None:
                search_record.rating_value = scraped_data['rating_value']
            if scraped_data.get('rating_count') is not None:
                search_record.rating_count = scraped_data['rating_count']
            if scraped_data.get('description'):
                search_record.scraped_description = scraped_data['description']
            
            search_record.last_scraped_at = timezone.now()
            search_record.scrape_data = scraped_data  # Store raw scraped data
            
            # Use scraped level if not available from Steam API
            if not search_record.level and scraped_data.get('steam_level'):
                search_record.level = scraped_data['steam_level']
            
            # Override ban data with scraped data if more detailed
            if scraped_data.get('vac_banned') is not None:
                if scraped_data.get('vac_bans_count'):
                    search_record.vac_bans = scraped_data['vac_bans_count']
            if scraped_data.get('game_banned') is not None:
                if scraped_data.get('game_bans_count'):
                    search_record.game_bans = scraped_data['game_bans_count']
            if scraped_data.get('community_banned') is not None:
                search_record.community_banned = scraped_data['community_banned']
            if scraped_data.get('trade_banned') is not None:
                search_record.trade_ban = 'Banned' if scraped_data['trade_banned'] else 'None'
        
        search_record.save()
        
        # Detect changes
        changes = self._detect_changes(previous_data, search_record)
        
        # Create history entry
        history = SteamProfileHistory.objects.create(
            search=search_record,
            searched_by=user,
            persona_name=search_record.persona_name,
            avatar_url=search_record.avatar_url,
            profile_state=search_record.profile_state,
            vac_bans=search_record.vac_bans,
            game_bans=search_record.game_bans,
            days_since_last_ban=search_record.days_since_last_ban,
            changes_detected=changes
        )
        
        # Get ALL related templates
        from .models import (BanExtensionTemplate, PlayerReportTemplate,
                             RefundTemplate, StaffApplicationResponse)
        
        refund_templates = RefundTemplate.objects.filter(
            steam_id_64=steam_id_64
        ).select_related('created_by').order_by('-created_at')
        
        ban_extensions = BanExtensionTemplate.objects.filter(
            steam_id_64=steam_id_64
        ).select_related('submitted_by', 'approved_by').order_by('-ban_expires_at', '-created_at')
        
        player_reports = PlayerReportTemplate.objects.filter(
            steam_id_64=steam_id_64
        ).select_related('handled_by').order_by('-created_at')
        
        staff_apps = StaffApplicationResponse.objects.filter(
            steam_id_64=steam_id_64
        ).select_related('reviewed_by').order_by('-created_at')
        
        # Get search history
        search_history = SteamProfileHistory.objects.filter(
            search=search_record
        ).select_related('searched_by').order_by('-searched_at')[:20]
        
        # Build response
        return {
            'steam_id': steam_id_converted,
            'steam_id_64': steam_id_64,
            'profile': self._build_profile_dict(search_record),
            'bans': {
                'vac_bans': search_record.vac_bans,
                'game_bans': search_record.game_bans,
                'days_since_last_ban': search_record.days_since_last_ban,
                'community_banned': search_record.community_banned,
                'trade_ban': search_record.trade_ban,
            },
            'search_stats': {
                'total_searches': search_record.search_count,
                'first_searched': search_record.first_searched_at,
                'last_searched': search_record.last_searched_at,
                'last_searched_by': user.username if user else None,
            },
            'changes': changes,
            'related_templates': {
                'refunds': self._serialize_templates(refund_templates, 'refund'),
                'ban_extensions': self._serialize_templates(ban_extensions, 'ban_extension'),
                'player_reports': self._serialize_templates(player_reports, 'player_report'),
                'staff_applications': self._serialize_templates(staff_apps, 'staff_application'),
            },
            'search_history': self._serialize_history(search_history),
        }
    
    def _convert_to_steam_id_64(self, steam_id):
        """Convert any Steam ID format to Steam ID 64."""
        # If already Steam ID 64
        if steam_id.isdigit() and len(steam_id) == 17:
            return steam_id
        
        # If STEAM_X:Y:Z format
        if steam_id.startswith('STEAM_'):
            parts = steam_id.replace('STEAM_', '').split(':')
            if len(parts) == 3:
                y = int(parts[1])
                z = int(parts[2])
                return str(76561197960265728 + (z * 2) + y)
        
        # If [U:1:XXXXXX] format
        if steam_id.startswith('[U:1:'):
            account_id = int(steam_id.replace('[U:1:', '').replace(']', ''))
            return str(76561197960265728 + account_id)
        
        return steam_id
    
    def _convert_to_steam_id(self, steam_id_64):
        """Convert Steam ID 64 to STEAM_X:Y:Z format."""
        try:
            steam_id_int = int(steam_id_64)
            account_id = steam_id_int - 76561197960265728
            y = account_id % 2
            z = (account_id - y) // 2
            return f"STEAM_0:{y}:{z}"
        except (ValueError, TypeError):
            return steam_id_64
    
    def _convert_to_steam_id_3(self, steam_id_64):
        """Convert Steam ID 64 to SteamID3 [U:1:XXXXX] format."""
        try:
            steam_id_int = int(steam_id_64)
            account_id = steam_id_int - 76561197960265728
            return f"[U:1:{account_id}]"
        except (ValueError, TypeError):
            return ""
    
    def _get_persona_state_text(self, state):
        """Convert persona state integer to readable text."""
        states = {
            0: 'Offline',
            1: 'Online',
            2: 'Busy',
            3: 'Away',
            4: 'Snooze',
            5: 'Looking to trade',
            6: 'Looking to play',
        }
        return states.get(state, 'Unknown')
    
    def _fetch_steam_api_data(self, steam_id_64):
        """Fetch profile data from Steam API."""
        if not self.steam_api_key:
            return None
        
        try:
            response = requests.get(
                "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/",
                params={
                    'key': self.steam_api_key,
                    'steamids': steam_id_64
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                players = data.get('response', {}).get('players', [])
                if players:
                    player = players[0]
                    print(f"Steam API Response for {steam_id_64}:")
                    print(f"  - avatarfull: {player.get('avatarfull')}")
                    print(f"  - avatar: {player.get('avatar')}")
                    print(f"  - avatarmedium: {player.get('avatarmedium')}")
                    return player
                return None
        except Exception as e:
            print(f"Error fetching Steam API data: {e}")
        
        return None
    
    def _fetch_scraped_data(self, steam_id_64):
        """Fetch enhanced profile data from steamid.pro and steamid.io scrapers."""
        try:
            # Get data from steamid.pro (avatar, rating, etc.)
            scraped_data_pro = scrape_steamid_profile(steam_id_64)
            
            # Get data from steamid.io (account_name, profile_created, profile_state)
            scraped_data_io = scrape_steamid_io(steam_id_64)
            
            # Merge the data - steamid.io overrides steamid.pro for overlapping fields
            scraped_data = scraped_data_pro or {}
            if scraped_data_io:
                scraped_data.update(scraped_data_io)
            
            if scraped_data:
                print(f"Scraped data for {steam_id_64}:")
                print(f"  - avatar_url: {scraped_data.get('avatar_url')}")
                print(f"  - display_name: {scraped_data.get('display_name')}")
                print(f"  - account_name: {scraped_data.get('account_name')}")
                print(f"  - profile_created: {scraped_data.get('profile_created')}")
                print(f"  - profile_state: {scraped_data.get('profile_state')}")
                print(f"  - vanity_url: {scraped_data.get('vanity_url')}")
                print(f"  - estimated_value: {scraped_data.get('estimated_value')}")
            return scraped_data if scraped_data else None
        except Exception as e:
            print(f"Error scraping profile data: {e}")
            return None
    
    def _fetch_ban_data(self, steam_id_64):
        """Fetch ban information from Steam API."""
        if not self.steam_api_key:
            return None
        
        try:
            response = requests.get(
                "https://api.steampowered.com/ISteamUser/GetPlayerBans/v1/",
                params={
                    'key': self.steam_api_key,
                    'steamids': steam_id_64
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                players = data.get('players', [])
                return players[0] if players else None
        except Exception as e:
            print(f"Error fetching ban data: {e}")
        
        return None
    
    def _get_profile_state(self, profile_data):
        """Determine profile visibility state."""
        visibility = profile_data.get('communityvisibilitystate', 1)
        if visibility == 3:
            return 'public'
        elif visibility == 2:
            return 'friends_only'
        else:
            return 'private'
    
    def _add_to_past_names(self, search_record, new_name):
        """Add a name to the past_names list if it's unique."""
        if not new_name or not new_name.strip():
            return
        
        # Initialize past_names if not set
        if not isinstance(search_record.past_names, list):
            search_record.past_names = []
        
        # Check if name already exists
        existing_names = [entry['name'] for entry in search_record.past_names if isinstance(entry, dict)]
        if new_name not in existing_names:
            search_record.past_names.append({
                'name': new_name,
                'first_seen': timezone.now().isoformat(),
                'last_seen': timezone.now().isoformat()
            })
        else:
            # Update last_seen for existing name
            for entry in search_record.past_names:
                if isinstance(entry, dict) and entry.get('name') == new_name:
                    entry['last_seen'] = timezone.now().isoformat()
                    break
    
    def _detect_changes(self, previous_data, current_record):
        """Detect changes between previous and current data."""
        changes = {}
        
        if previous_data['persona_name'] and previous_data['persona_name'] != current_record.persona_name:
            changes['persona_name'] = {
                'old': previous_data['persona_name'],
                'new': current_record.persona_name
            }
        
        if previous_data['vac_bans'] != current_record.vac_bans:
            changes['vac_bans'] = {
                'old': previous_data['vac_bans'],
                'new': current_record.vac_bans
            }
        
        if previous_data['game_bans'] != current_record.game_bans:
            changes['game_bans'] = {
                'old': previous_data['game_bans'],
                'new': current_record.game_bans
            }
        
        if previous_data['profile_state'] and previous_data['profile_state'] != current_record.profile_state:
            changes['profile_state'] = {
                'old': previous_data['profile_state'],
                'new': current_record.profile_state
            }
        
        return changes
    
    def _build_profile_dict(self, search_record):
        """Build profile dictionary from search record."""
        return {
            # Basic info
            'name': search_record.persona_name,
            'account_name': search_record.account_name,
            'profile_url': search_record.profile_url,
            'avatar_url': search_record.avatar_url,
            'profile_state': search_record.profile_state,
            'real_name': search_record.real_name,
            
            # Steam IDs
            'steam_id_3': search_record.steam_id_3,
            'custom_url': search_record.custom_url if search_record.custom_url and not search_record.custom_url.isdigit() else None,
            
            # Status
            'persona_state': search_record.persona_state,
            'persona_state_text': self._get_persona_state_text(search_record.persona_state),
            'last_logoff': search_record.last_logoff,
            
            # Location
            'location': search_record.location,
            'country_code': search_record.country_code,
            'state_code': search_record.state_code,
            
            # Game info (if playing)
            'game_id': search_record.game_id,
            'game_extra_info': search_record.game_extra_info,
            'game_server_ip': search_record.game_server_ip,
            
            # Account details
            'is_private': search_record.is_private,
            'is_limited': search_record.is_limited,
            'level': search_record.level,
            'account_created': search_record.account_created,
            'comment_permission': search_record.comment_permission,
            
            # Enhanced scraped data from steamid.pro
            'vanity_url': search_record.vanity_url,
            'account_id': search_record.account_id,
            'steam_id_2': search_record.steam_id_2,
            'invite_url': search_record.invite_url,
            'invite_url_short': search_record.invite_url_short,
            'fivem_hex': search_record.fivem_hex,
            'online_status': search_record.online_status,
            'estimated_value': search_record.estimated_value,
            'rating_value': search_record.rating_value,
            'rating_count': search_record.rating_count,
            'scraped_description': search_record.scraped_description,
            'last_scraped_at': search_record.last_scraped_at,
            
            # Past names tracking
            'past_names': search_record.past_names if isinstance(search_record.past_names, list) else [],
        }
    
    def _serialize_templates(self, templates, template_type):
        """Serialize related templates based on type."""
        result = []
        
        for t in templates:
            base = {
                'id': t.id,
                'type': template_type,
                'created_at': t.created_at,
                'updated_at': t.updated_at,
            }
            
            if template_type == 'refund':
                base.update({
                    'ticket_number': t.ticket_number,
                    'status': t.status,
                    'player_ign': t.player_ign,
                    'server': t.server,
                    'items_lost': t.items_lost[:100] + '...' if len(t.items_lost) > 100 else t.items_lost,
                    'created_by': t.created_by.username if t.created_by else None,
                })
            elif template_type == 'ban_extension':
                base.update({
                    'player_ign': t.player_ign,
                    'ban_reason': t.ban_reason[:100] + '...' if len(t.ban_reason) > 100 else t.ban_reason,
                    'status': t.status,
                    'current_ban_time': t.current_ban_time,
                    'required_ban_time': t.required_ban_time,
                    'is_active_ban': t.is_active_ban,
                    'ban_expires_at': t.ban_expires_at,
                    'submitted_by': t.submitted_by.username if t.submitted_by else None,
                })
            elif template_type == 'player_report':
                base.update({
                    'player_ign': t.player_ign,
                    'status': t.status,
                    'action_taken': t.action_taken,
                    'case_link': t.case_link,
                    'decision_reason': t.decision_reason[:100] + '...' if len(t.decision_reason) > 100 else t.decision_reason,
                    'handled_by': t.handled_by.username if t.handled_by else None,
                })
            elif template_type == 'staff_application':
                base.update({
                    'applicant_name': t.applicant_name,
                    'rating': t.rating,
                    'rating_stars': t.rating_stars,
                    'recommend_hire': t.recommend_hire,
                    'reviewed_by': t.reviewed_by.username if t.reviewed_by else None,
                })
            
            result.append(base)
        
        return result
    
    def _serialize_history(self, history):
        """Serialize search history."""
        return [{
            'searched_at': h.searched_at,
            'searched_by': h.searched_by.username if h.searched_by else 'Unknown',
            'persona_name': h.persona_name,
            'vac_bans': h.vac_bans,
            'game_bans': h.game_bans,
            'changes': h.changes_detected,
        } for h in history]
