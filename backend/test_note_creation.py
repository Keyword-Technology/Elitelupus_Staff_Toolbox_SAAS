import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from datetime import datetime, timedelta

from apps.accounts.models import User
from apps.templates_manager.models import SteamProfileNote, SteamProfileSearch
from apps.templates_manager.services import SteamLookupService
from django.utils import timezone

# Get or create a test user
user, _ = User.objects.get_or_create(
    username='testuser',
    defaults={'display_name': 'Test User'}
)

# Test Steam ID
test_steam_id = '76561199013656172'

# Lookup profile
service = SteamLookupService()
print("Looking up profile...")
profile_data = service.lookup_profile(test_steam_id, user=user)

print(f"\nProfile data keys: {profile_data.keys()}")
print(f"ID: {profile_data.get('id')}")
print(f"Steam ID 64: {profile_data.get('steam_id_64')}")

# Get the SteamProfileSearch object
steam_profile = SteamProfileSearch.objects.get(steam_id_64=test_steam_id)
print(f"\nSteamProfileSearch ID: {steam_profile.id}")

# Try to create a note
print("\nCreating test note...")
try:
    expires_at = timezone.now() + timedelta(hours=24)
    note = SteamProfileNote.objects.create(
        steam_profile=steam_profile,
        author=user,
        note_type='general',
        title='Test Note',
        content='This is a test note',
        severity=1,
        server='Server 1',
        expires_at=expires_at
    )
    print(f"✓ Note created successfully! ID: {note.id}")
    
    # Clean up
    note.delete()
    print("✓ Test note deleted")
    
except Exception as e:
    print(f"✗ Error creating note: {e}")

print("\n✓ All tests completed!")
