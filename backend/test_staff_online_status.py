"""
Test script to verify staff roster online status detection.
"""
import os

import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.servers.models import GameServer, ServerPlayer
from apps.servers.services import ServerQueryService
from apps.staff.models import StaffRoster


def test_online_status():
    """Test that staff roster correctly detects online status."""
    print("=" * 70)
    print("Testing Staff Roster Online Status Detection")
    print("=" * 70)
    
    # Query the server first to update player data
    print("\nQuerying servers...")
    service = ServerQueryService()
    servers = GameServer.objects.filter(is_active=True)
    
    for server in servers:
        service.query_server(server)
    
    print("✓ Server query complete\n")
    
    # Get Cloudyman from roster
    cloudyman = StaffRoster.objects.filter(name__icontains='cloudyman').first()
    
    if not cloudyman:
        print("✗ Cloudyman not found in staff roster")
        return
    
    print(f"Staff Member: {cloudyman.name} ({cloudyman.rank})")
    print(f"Steam ID: {cloudyman.steam_id}")
    
    # Check if found in ServerPlayer using steam_id
    if cloudyman.steam_id:
        players = ServerPlayer.objects.filter(
            steam_id=cloudyman.steam_id,
            is_staff=True
        )
        
        print(f"\nServerPlayer Query (by steam_id):")
        print(f"  Found: {players.exists()}")
        
        if players.exists():
            p = players.first()
            print(f"  ✓ In-Game Name: {p.name}")
            print(f"  ✓ Server: {p.server.name}")
            print(f"  ✓ Is Staff: {p.is_staff}")
            print(f"  ✓ Staff Rank: {p.staff_rank}")
            print(f"  ✓ Duration: {p.duration_formatted}")
        else:
            print("  ✗ Not found in ServerPlayer")
    else:
        print("\n✗ No Steam ID available for this staff member")
    
    # Test the serializer method
    print("\n" + "=" * 70)
    print("Testing StaffRosterSerializer Methods")
    print("=" * 70)
    
    from apps.staff.serializers import StaffRosterSerializer
    
    serializer = StaffRosterSerializer(cloudyman)
    
    print(f"\nget_is_online(): {serializer.get_is_online(cloudyman)}")
    print(f"get_server_name(): {serializer.get_server_name(cloudyman)}")
    print(f"get_server_id(): {serializer.get_server_id(cloudyman)}")
    
    # Test full serialized data
    print("\n" + "=" * 70)
    print("Full Serialized Data")
    print("=" * 70)
    
    data = serializer.data
    print(f"\nUsername: {data.get('username')}")
    print(f"Role: {data.get('role')}")
    print(f"Is Online: {data.get('is_online')}")
    print(f"Server Name: {data.get('server_name')}")
    print(f"Server ID: {data.get('server_id')}")
    
    print("\n" + "=" * 70)
    print("Test Complete!")
    print("=" * 70)

if __name__ == '__main__':
    test_online_status()
