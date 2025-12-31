"""
SteamID.io Scraper Service
Extracts account name and other data not available from Steam API.
"""
import logging
import re
from typing import Any, Dict, Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class SteamIDIOScraper:
    """
    Scraper for steamid.io website to get account login name.
    This site provides the account name which is not available from Steam API.
    """
    
    BASE_URL = "https://steamid.io/lookup/"
    
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
        Fetch and parse Steam profile from steamid.io
        
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
            except:
                soup = BeautifulSoup(response.content, 'html.parser')
            
            data = {}
            
            # Extract account name from the page
            # Look for: <li>name <span>hessconnor41</span></li>
            account_name = self._extract_account_name(soup)
            if account_name:
                data['account_name'] = account_name
            
            # Also extract profile created date
            profile_created = self._extract_profile_created(soup)
            if profile_created:
                data['profile_created'] = profile_created
            
            # Extract profile state
            profile_state = self._extract_profile_state(soup)
            if profile_state:
                data['profile_state'] = profile_state
            
            logger.info(f"Scraped steamid.io data for {steam_id_64}: {data}")
            return data if data else None
            
        except requests.RequestException as e:
            logger.error(f"Error fetching steamid.io data for {steam_id_64}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing steamid.io data for {steam_id_64}: {e}")
            return None
    
    def _extract_account_name(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract account name (login name) from the page.
        Looking for: <li>name <span>hessconnor41</span></li>
        """
        try:
            # Strategy 1: Find li containing "name" text followed by span
            for li in soup.find_all('li'):
                text = li.get_text(strip=True)
                if text.startswith('name'):
                    span = li.find('span')
                    if span:
                        account_name = span.get_text(strip=True)
                        if account_name and not account_name.startswith('name'):
                            return account_name
            
            # Strategy 2: Find by data attribute or class patterns
            name_span = soup.find('span', {'class': re.compile(r'account.*name', re.I)})
            if name_span:
                return name_span.get_text(strip=True)
            
            # Strategy 3: Look in definition list
            dts = soup.find_all('dt')
            for dt in dts:
                if 'name' in dt.get_text(strip=True).lower():
                    dd = dt.find_next_sibling('dd')
                    if dd:
                        return dd.get_text(strip=True)
            
            return None
        except Exception as e:
            logger.debug(f"Error extracting account name: {e}")
            return None
    
    def _extract_profile_created(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract profile created date from the page.
        Looking for: <li>profile created <span>December 22, 2019</span></li>
        """
        try:
            # Strategy 1: Find li containing "profile created" text
            for li in soup.find_all('li'):
                text = li.get_text(strip=True)
                if 'profile created' in text.lower():
                    span = li.find('span')
                    if span:
                        date_str = span.get_text(strip=True)
                        if date_str:
                            return date_str
            
            # Strategy 2: Look in definition list
            dts = soup.find_all('dt')
            for dt in dts:
                if 'profile created' in dt.get_text(strip=True).lower():
                    dd = dt.find_next_sibling('dd')
                    if dd:
                        return dd.get_text(strip=True)
            
            return None
        except Exception as e:
            logger.debug(f"Error extracting profile created: {e}")
            return None
    
    def _extract_profile_state(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract profile state (public/private) from the page.
        Looking for: <li>profile state <span>public</span></li>
        """
        try:
            # Strategy 1: Find li containing "profile state" text
            for li in soup.find_all('li'):
                text = li.get_text(strip=True)
                if 'profile state' in text.lower():
                    span = li.find('span')
                    if span:
                        state = span.get_text(strip=True).lower()
                        if state in ['public', 'private', 'friends only']:
                            return state
            
            # Strategy 2: Look in definition list
            dts = soup.find_all('dt')
            for dt in dts:
                if 'profile state' in dt.get_text(strip=True).lower():
                    dd = dt.find_next_sibling('dd')
                    if dd:
                        return dd.get_text(strip=True).lower()
            
            return None
        except Exception as e:
            logger.debug(f"Error extracting profile state: {e}")
            return None


# Helper function for easy import
def scrape_steamid_io(steam_id_64: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to scrape steamid.io data.
    
    Args:
        steam_id_64: The 64-bit Steam ID
        
    Returns:
        Dictionary with account_name, profile_created, profile_state or None
    """
    scraper = SteamIDIOScraper()
    return scraper.fetch_profile(steam_id_64)
