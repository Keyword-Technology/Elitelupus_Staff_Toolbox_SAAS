"""
Quick test to verify Steam note creation works end-to-end.
This script tests the complete flow without needing the frontend.
"""

import os
import sys
from datetime import timedelta

import django
from django.utils import timezone

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.templates_manager.models import SteamProfileNote, SteamProfileSearch
from apps.templates_manager.services import SteamLookupService
from django.contrib.auth import get_user_model

User = get_user_model()

def test_steam_note_creation():
    print("\n" + "="*60)
    print("Testing Steam Note Creation Flow")
    print("="*60)
    
    # Step 1: Get or create test user
    print("\n[1] Getting test user...")
    user, created = User.objects.get_or_create(
        username='test_admin',
        defaults={
            'email': 'test@example.com',
            'is_staff': True,
            'is_superuser': True,
            'staff_role': 'SYSADMIN'
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
    print(f"   ✓ User: {user.username} (ID: {user.id})")
    
    # Step 2: Test Steam profile lookup
    print("\n[2] Testing Steam profile lookup...")
    test_steam_id = "76561198123456789"  # Example Steam ID
    
    try:
        service = SteamLookupService()
        profile_data = service.lookup_profile(test_steam_id, user)
        
        print(f"   ✓ Profile lookup successful")
        print(f"   ✓ Profile ID: {profile_data.get('id')}")
        print(f"   ✓ Steam ID 64: {profile_data.get('steam_id_64')}")
        
        # Verify id field is present
        if 'id' not in profile_data:
            print("   ✗ ERROR: 'id' field missing from profile data!")
            return False
        
        steam_profile_id = profile_data['id']
        print(f"   ✓ Profile data includes 'id' field: {steam_profile_id}")
        
    except Exception as e:
        print(f"   ✗ Profile lookup failed: {e}")
        return False
    
    # Step 3: Create a test note using the profile ID
    print("\n[3] Creating test note...")
    
    try:
        steam_profile = SteamProfileSearch.objects.get(id=steam_profile_id)
        
        expires_at = timezone.now() + timedelta(hours=24)
        
        note = SteamProfileNote.objects.create(
            steam_profile=steam_profile,
            author=user,
            note_type='general',
            title='Test Note',
            content='This is a test note to verify the fix works.',
            severity=2,
            server='Server 1',
            expires_at=expires_at
        )
        
        print(f"   ✓ Note created successfully!")
        print(f"   ✓ Note ID: {note.id}")
        print(f"   ✓ Title: {note.title}")
        print(f"   ✓ Severity: {note.severity}")
        print(f"   ✓ Expires: {note.expires_at}")
        print(f"   ✓ Steam Profile ID: {note.steam_profile.id}")
        
    except Exception as e:
        print(f"   ✗ Note creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 4: Verify the note can be retrieved
    print("\n[4] Verifying note retrieval...")
    
    try:
        notes = SteamProfileNote.objects.filter(
            steam_profile__steam_id_64=test_steam_id
        )
        
        print(f"   ✓ Found {notes.count()} note(s) for this Steam profile")
        
        for n in notes:
            print(f"      - {n.title} (Severity: {n.severity})")
        
    except Exception as e:
        print(f"   ✗ Note retrieval failed: {e}")
        return False
    
    # Step 5: Cleanup (delete test note)
    print("\n[5] Cleaning up...")
    
    try:
        note.delete()
        print(f"   ✓ Test note deleted")
        
    except Exception as e:
        print(f"   ⚠ Cleanup failed: {e}")
    
    print("\n" + "="*60)
    print("✓ All tests completed successfully!")
    print("="*60)
    print("\n✅ The fix is working correctly!")
    print("   - Backend returns profile ID")
    print("   - Profile can be looked up by ID")
    print("   - Notes can be created with integer steam_profile FK")
    print("\nYou can now test in the frontend:")
    print("   1. Restart your backend server")
    print("   2. Do a fresh Steam lookup")
    print("   3. Create a note - it should work!\n")
    
    return True

if __name__ == '__main__':
    try:
        success = test_steam_note_creation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
