"""
Test that verifies staff roster API shows correct online status.
"""
import os

import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.servers.models import ServerPlayer
from apps.staff.models import StaffRoster
from apps.staff.serializers import StaffRosterSerializer


def test_staff_roster_api():
    """Test staff roster serializer with current online staff."""
    print("=" * 70)
    print("Staff Roster API Online Status Test")
    print("=" * 70)
    
    # Get all staff from ServerPlayer (currently online)
    online_players = ServerPlayer.objects.filter(is_staff=True)
    
    print(f"\nCurrently Online Staff (from ServerPlayer): {online_players.count()}")
    for player in online_players:
        print(f"  - {player.name} | Steam ID: {player.steam_id} | {player.server.name}")
    
    print("\n" + "=" * 70)
    print("Testing Serializer for Each Online Staff Member")
    print("=" * 70)
    
    for player in online_players:
        print(f"\n{'=' * 70}")
        print(f"Testing: {player.name}")
        print(f"{'=' * 70}")
        
        # Find matching staff roster entry
        roster = None
        if player.steam_id:
            roster = StaffRoster.objects.filter(steam_id=player.steam_id).first()
        
        if not roster:
            print(f"  ✗ No roster entry found for {player.name}")
            continue
        
        print(f"  ✓ Found roster entry: {roster.name} ({roster.rank})")
        print(f"  Steam ID: {roster.steam_id}")
        
        # Test serializer
        serializer = StaffRosterSerializer(roster)
        data = serializer.data
        
        print(f"\n  Serializer Output:")
        print(f"    username: {data.get('username')}")
        print(f"    role: {data.get('role')}")
        print(f"    is_online: {data.get('is_online')} {'✓' if data.get('is_online') else '✗'}")
        print(f"    server_name: {data.get('server_name')}")
        print(f"    server_id: {data.get('server_id')}")
        
        # Verify correctness
        if data.get('is_online'):
            print(f"  ✓ Online status CORRECT")
        else:
            print(f"  ✗ Online status INCORRECT (should be True)")
        
        if data.get('server_name') == player.server.name:
            print(f"  ✓ Server name CORRECT")
        else:
            print(f"  ✗ Server name INCORRECT (expected {player.server.name})")
    
    print("\n" + "=" * 70)
    print("Test Complete!")
    print("=" * 70)

if __name__ == '__main__':
    test_staff_roster_api()
