"""
SteamID.pro Scraper Service
Reverse-engineered from HTML structure to extract Steam profile data.
Uses multiple fallback strategies to be resilient to page changes.
"""
import logging
import re
from datetime import datetime
from typing import Any, Dict, Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class SteamIDProScraper:
    """
    Scraper for steamid.pro website.
    Designed to be resilient by using multiple extraction strategies:
    1. Schema.org structured data (most reliable)
    2. Meta tags (og:image, etc.)
    3. Specific HTML selectors (class names, IDs)
    4. Pattern matching in text content
    5. Table row patterns
    """
    
    BASE_URL = "https://steamid.pro/lookup/"
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def fetch_profile(self, steam_id_64: str) -> Optional[Dict[str, Any]]:
        """
        Fetch and parse Steam profile from steamid.pro
        
        Args:
            steam_id_64: The 64-bit Steam ID
            
        Returns:
            Dictionary with extracted data or None if failed
        """
        url = f"{self.BASE_URL}{steam_id_64}"
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Try lxml first, fall back to html.parser
            try:
                soup = BeautifulSoup(response.content, 'lxml')
            except Exception:
                soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract data using multiple strategies
            data = {
                'steamid64': steam_id_64,
                'scraped_at': datetime.now().isoformat(),
                'source_url': url
            }
            
            # Strategy 1: Schema.org structured data (most reliable)
            data.update(self._extract_schema_data(soup))
            
            # Strategy 2: Meta tags
            data.update(self._extract_meta_tags(soup))
            
            # Strategy 3: Profile header section
            data.update(self._extract_header_data(soup))
            
            # Strategy 4: SteamID table
            data.update(self._extract_steamid_table(soup))
            
            # Strategy 5: Bans and restrictions
            data.update(self._extract_bans_data(soup))
            
            # Strategy 6: Price/value data
            data.update(self._extract_price_data(soup))
            
            # Strategy 7: Rating data
            data.update(self._extract_rating_data(soup))
            
            # Strategy 8: Level data
            data.update(self._extract_level_data(soup))
            
            logger.info(f"Successfully scraped profile for {steam_id_64}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch steamid.pro page for {steam_id_64}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing steamid.pro data for {steam_id_64}: {e}")
            return None
    
    def _extract_schema_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract data from Schema.org JSON-LD structured data"""
        data = {}
        
        try:
            # Find schema.org script tag
            schema_script = soup.find('script', type='application/ld+json')
            if schema_script:
                import json
                schema_data = json.loads(schema_script.string)
                
                # Extract from Product schema
                if schema_data.get('@type') == 'Product':
                    data['display_name'] = schema_data.get('name', '')
                    data['avatar_url'] = schema_data.get('image', '')
                    data['description'] = schema_data.get('description', '')
                    
                    # Extract rating
                    if 'aggregateRating' in schema_data:
                        rating = schema_data['aggregateRating']
                        data['rating_value'] = float(rating.get('ratingValue', 0))
                        data['rating_count'] = int(rating.get('reviewCount', 0))
                    
                    # Extract price
                    if 'offers' in schema_data:
                        offers = schema_data['offers']
                        data['estimated_value'] = offers.get('price', '')
                        data['currency'] = offers.get('priceCurrency', 'USD')
        except Exception as e:
            logger.debug(f"Schema.org extraction failed: {e}")
        
        return data
    
    def _extract_meta_tags(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract data from meta tags"""
        data = {}
        
        try:
            # og:image meta tag (avatar fallback)
            og_image = soup.find('meta', property='og:image')
            if og_image and not data.get('avatar_url'):
                data['avatar_url'] = og_image.get('content', '')
            
            # og:title (name fallback)
            og_title = soup.find('meta', property='og:title')
            if og_title:
                title = og_title.get('content', '')
                # Extract name from title like "Connor2 | Steam ID:76561199012665547..."
                name_match = re.match(r'^([^|]+)', title)
                if name_match and not data.get('display_name'):
                    data['display_name'] = name_match.group(1).strip()
            
            # Description
            og_desc = soup.find('meta', property='og:description')
            if og_desc and not data.get('description'):
                data['description'] = og_desc.get('content', '')
        except Exception as e:
            logger.debug(f"Meta tag extraction failed: {e}")
        
        return data
    
    def _extract_header_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract data from profile header section"""
        data = {}
        
        try:
            # Find header-player section
            header = soup.find('div', class_='header-player')
            if header:
                # Avatar image - try multiple selectors
                avatar_img = header.find('img', id='img-uploaded')
                if not avatar_img:
                    # Fallback: find any avatar image in header
                    avatar_img = header.find('img', class_='avatar-xl')
                if not avatar_img:
                    # Fallback: find any img with steamstatic in src
                    avatar_img = header.find('img', src=re.compile(r'avatars\.steamstatic\.com'))
                
                if avatar_img:
                    avatar_url = avatar_img.get('src', '')
                    if avatar_url and 'steamstatic.com' in avatar_url:
                        data['avatar_url'] = avatar_url
                        logger.info(f"Found avatar URL: {avatar_url}")
                
                # Display name from h1
                h1 = header.find('h1')
                if not h1:
                    h1 = header.find('h1', class_='mb-0')
                if h1:
                    data['display_name'] = h1.get_text(strip=True)
                    logger.info(f"Found display name: {data['display_name']}")
                
                # Player info list (level, status)
                player_info = header.find('ul', class_='player-info')
                if player_info:
                    items = player_info.find_all('li')
                    for item in items:
                        text = item.get_text(strip=True).lower()
                        
                        # Extract level
                        if text.startswith('level'):
                            level_match = re.search(r'level\s+(\d+)', text)
                            if level_match:
                                data['steam_level'] = int(level_match.group(1))
                        
                        # Extract online status
                        elif text in ['online', 'offline', 'in-game']:
                            data['online_status'] = text
            else:
                logger.warning("header-player div not found")
                
                # Fallback: try to find avatar anywhere on page
                avatar_img = soup.find('img', src=re.compile(r'avatars\.steamstatic\.com.*_full'))
                if avatar_img:
                    data['avatar_url'] = avatar_img.get('src', '')
                    logger.info(f"Found avatar via fallback: {data['avatar_url']}")
                    
        except Exception as e:
            logger.debug(f"Header extraction failed: {e}")
        
        return data
    
    def _extract_steamid_table(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract SteamID formats from the table"""
        data = {}
        
        try:
            # Find all tables with class rtable
            tables = soup.find_all('table', class_='rtable')
            
            for table in tables:
                rows = table.find_all('tr')
                
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True).lower()
                        value = cells[1].get_text(strip=True)
                        
                        # Remove copy icon from value
                        value = re.sub(r'\s*Click to copy!.*$', '', value)
                        
                        # Map table labels to data fields
                        if 'vanity url' in label or 'custom url' in label:
                            data['vanity_url'] = value
                        elif label == 'accountid':
                            data['account_id'] = value
                        elif label == 'steamid':
                            data['steam_id_64'] = value
                        elif 'steam2' in label:
                            data['steam_id_2'] = value
                        elif 'steam3' in label:
                            data['steam_id_3'] = value
                        elif 'invite url' in label and 'short' not in label:
                            data['invite_url'] = value
                        elif 'invite url' in label and 'short' in label:
                            data['invite_url_short'] = value
                        elif 'fivem' in label or 'hex' in label:
                            data['fivem_hex'] = value
        except Exception as e:
            logger.debug(f"SteamID table extraction failed: {e}")
        
        return data
    
    def _extract_bans_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract ban status information including ban dates"""
        data = {
            'vac_banned': False,
            'game_banned': False,
            'community_banned': False,
            'trade_banned': False,
            'vac_ban_dates': []  # List of VAC ban dates
        }
        
        try:
            # Find bans table by heading
            bans_heading = soup.find('h4', string=re.compile(r'Bans and restrictions', re.I))
            if bans_heading:
                bans_table = bans_heading.find_next('table', class_='rtable')
                
                if bans_table:
                    rows = bans_table.find_all('tr')
                    
                    for row in rows:
                        cells = row.find_all('td')
                        if len(cells) >= 2:
                            label = cells[0].get_text(strip=True).lower()
                            value_cell = cells[1]
                            value_text = value_cell.get_text(strip=True).lower()
                            
                            # Check if it's a ban (not "in good standing" or "green" class)
                            is_banned = 'good standing' not in value_text and 'green' not in value_cell.get('class', [])
                            
                            if 'game ban' in label:
                                data['game_banned'] = is_banned
                                if is_banned:
                                    # Extract number of bans
                                    num_match = re.search(r'(\d+)', value_text)
                                    if num_match:
                                        data['game_bans_count'] = int(num_match.group(1))
                            elif 'vac ban' in label:
                                data['vac_banned'] = is_banned
                                if is_banned:
                                    num_match = re.search(r'(\d+)', value_text)
                                    if num_match:
                                        data['vac_bans_count'] = int(num_match.group(1))
                                    
                                    # Extract VAC ban dates from the value cell
                                    # Look for dates in format like "Dec 23, 2024" or "23 Dec 2024"
                                    date_pattern = r'(\w+ \d{1,2},? \d{4})'
                                    dates = re.findall(date_pattern, value_cell.get_text())
                                    if dates:
                                        data['vac_ban_dates'] = dates
                                    
                                    # Also check for "X days ago" or "X day(s) ago" pattern
                                    days_ago_match = re.search(r'(\d+)\s+days?\s+ago', value_text)
                                    if days_ago_match and not dates:
                                        data['vac_ban_days_ago'] = int(days_ago_match.group(1))
                            elif 'community ban' in label:
                                data['community_banned'] = is_banned
                            elif 'trade ban' in label:
                                data['trade_banned'] = is_banned
        except Exception as e:
            logger.debug(f"Bans data extraction failed: {e}")
        
        return data
    
    def _extract_price_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract account value/price information"""
        data = {}
        
        try:
            # Find prices div
            prices_div = soup.find('div', class_='prices')
            if prices_div:
                # Extract numeric price
                price_span = prices_div.find('span', class_='number-price')
                if price_span:
                    price_text = price_span.get_text(strip=True)
                    # Extract number from "$1" format
                    price_match = re.search(r'[\$€£]?(\d+(?:\.\d+)?)', price_text)
                    if price_match:
                        data['estimated_value'] = price_match.group(1)
        except Exception as e:
            logger.debug(f"Price data extraction failed: {e}")
        
        return data
    
    def _extract_rating_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract user rating/review information"""
        data = {}
        
        try:
            # Find rating count
            rating_count_span = soup.find('span', id='ratingCount')
            if rating_count_span:
                data['rating_count'] = int(rating_count_span.get_text(strip=True))
            
            # Find rating value
            rating_value_span = soup.find('span', id='ratingValue')
            if rating_value_span:
                data['rating_value'] = float(rating_value_span.get_text(strip=True))
        except Exception as e:
            logger.debug(f"Rating data extraction failed: {e}")
        
        return data
    
    def _extract_level_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract Steam level from various sources"""
        data = {}
        
        try:
            # Look for level in player info
            if 'steam_level' not in data:
                # Try to find level anywhere in the page
                level_pattern = re.compile(r'Level\s+(\d+)', re.I)
                level_matches = soup.find_all(string=level_pattern)
                
                for match in level_matches:
                    level_search = level_pattern.search(match)
                    if level_search:
                        data['steam_level'] = int(level_search.group(1))
                        break
        except Exception as e:
            logger.debug(f"Level data extraction failed: {e}")
        
        return data


def scrape_steamid_profile(steam_id_64: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to scrape a Steam profile from steamid.pro
    
    Args:
        steam_id_64: The 64-bit Steam ID
        
    Returns:
        Dictionary with scraped data or None if failed
    """
    scraper = SteamIDProScraper()
    return scraper.fetch_profile(steam_id_64)
