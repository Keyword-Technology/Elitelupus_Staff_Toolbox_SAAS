#!/usr/bin/env python3
"""
Discord webhook notification script for server startup.
Sends a message to Discord when the server starts with version info.
"""
import configparser
import json
import os
import sys
from datetime import datetime, timezone
from urllib import error, request


def send_discord_notification(webhook_url, version, environment):
    """
    Send a Discord webhook notification about server startup.
    
    Args:
        webhook_url: The Discord webhook URL
        version: The server version string
        environment: The environment name (dev/prod)
    """
    if not webhook_url:
        print("⚠️  No Discord webhook URL provided, skipping notification")
        return False
    
    try:
        # Prepare the embed message
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Color codes: Green for startup
        color = 0x00FF00  # Green
        
        # Determine server name based on environment
        server_name = "Development Server" if environment == "development" else "Production Server"
        
        # Create the Discord embed with relative timestamp
        now_timestamp = int(datetime.now(timezone.utc).timestamp())
        data = {
            "embeds": [{
                "title": f"🚀 {server_name} Started",
                "description": f"The **Elitelupus Staff Toolbox** {server_name.lower()} has successfully started and is now online.",
                "color": color,
                "fields": [
                    {
                        "name": "📦 Version",
                        "value": f"`{version}`",
                        "inline": True
                    },
                    {
                        "name": "🌍 Environment",
                        "value": f"`{environment}`",
                        "inline": True
                    },
                    {
                        "name": "🕐 Startup Time",
                        "value": f"<t:{now_timestamp}:F>\n<t:{now_timestamp}:R>",
                        "inline": False
                    }
                ],
                "timestamp": timestamp,
                "footer": {
                    "text": "Elitelupus Staff Toolbox Backend"
                }
            }]
        }
        
        # Send the webhook
        req = request.Request(
            webhook_url,
            data=json.dumps(data).encode('utf-8'),
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'Elitelupus-Backend/1.0'
            },
            method='POST'
        )
        
        with request.urlopen(req, timeout=10) as response:
            if response.status == 204:
                print(f"✅ Discord notification sent successfully to {environment} channel")
                return True
            else:
                print(f"⚠️  Discord notification returned status {response.status}")
                return False
                
    except error.URLError as e:
        print(f"❌ Failed to send Discord notification: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error sending Discord notification: {e}")
        return False


def read_version_from_ini(ini_path=None):
    """
    Read the backend version from versions.ini file.
    
    Args:
        ini_path: Path to the versions.ini file (optional)
        
    Returns:
        str: Version string or "unknown" if not found
    """
    # Try multiple paths in order
    paths_to_try = [
        '/app/versions.ini',           # Docker container path
        'versions.ini',                 # Current directory
        './versions.ini',               # Explicit current directory
        os.path.join(os.path.dirname(__file__), '..', 'versions.ini'),  # Parent directory
        '../versions.ini'               # Parent directory alternative
    ]
    
    if ini_path:
        paths_to_try.insert(0, ini_path)
    
    for path in paths_to_try:
        if not os.path.exists(path):
            continue
            
        try:
            config = configparser.ConfigParser()
            config.read(path)
            
            if 'versions' in config and 'backend' in config['versions']:
                version = config['versions']['backend']
                print(f"✅ Read version from {path}: {version}")
                return version
        except Exception as e:
            print(f"⚠️  Error reading {path}: {e}")
            continue
    
    print("⚠️  Could not read version from versions.ini, using default")
    return "unknown"


if __name__ == '__main__':
    # Get webhook URL from environment variable
    webhook_url = os.environ.get('DISCORD_WEBHOOK_URL', '')
    
    # Get environment (default to development)
    environment = os.environ.get('ENVIRONMENT', 'development')
    
    # Read version from versions.ini
    version = read_version_from_ini()
    
    print("📢 Sending Discord startup notification...")
    
    # Send the notification
    success = send_discord_notification(webhook_url, version, environment)
    
    # Exit with appropriate code
    sys.exit(0 if success or not webhook_url else 1)
