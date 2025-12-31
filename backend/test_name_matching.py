"""
Test script for staff name matching with numbers.
Run this to verify the normalize_name function works correctly.
"""
import os

import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.servers.services import find_matching_staff, normalize_name
from apps.staff.models import StaffRoster


def test_normalize_name():
    """Test the normalize_name function with various inputs."""
    test_cases = [
        ('Cloudyman2', 'cloudyman'),
        ('2Cloudyman', 'cloudyman'),
        ('Admin123', 'admin'),
        ('Player', 'player'),
        ('Test99Player', 'test99player'),  # Only removes from start/end
        ('123Admin456', 'admin'),
        ('JohnDoe', 'johndoe'),
        ('  SpacedName  ', 'spacedname'),
        ('Name123456', 'name'),
    ]
    
    print("Testing normalize_name function:")
    print("-" * 50)
    
    all_passed = True
    for input_name, expected in test_cases:
        result = normalize_name(input_name)
        passed = result == expected
        status = "✓ PASS" if passed else "✗ FAIL"
        
        print(f"{status}: '{input_name}' -> '{result}' (expected: '{expected}')")
        
        if not passed:
            all_passed = False
    
    print("-" * 50)
    if all_passed:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed!")
    
    return all_passed


def test_staff_matching():
    """Test staff matching with actual database records."""
    print("\n\nTesting staff matching with database:")
    print("-" * 50)
    
    # Get all active staff
    staff = StaffRoster.objects.filter(is_active=True)
    
    if not staff.exists():
        print("⚠ No staff members found in database. Add some first.")
        return
    
    # Build staff roster dict
    staff_roster = {
        entry.name.lower(): entry 
        for entry in staff
    }
    
    print(f"Found {len(staff_roster)} staff members:")
    for name in staff_roster.keys():
        print(f"  - {name}")
    
    # Test cases with variations
    test_cases = [
        'Cloudyman',    # Exact match
        'Cloudyman2',   # With number at end
        '2Cloudyman',   # With number at start
        'cloudyman',    # Different case
        'CLOUDYMAN',    # All caps
        'NotAStaff',    # Should not match
    ]
    
    print("\nTesting player name matching:")
    for player_name in test_cases:
        match = find_matching_staff(player_name, staff_roster)
        if match:
            print(f"✓ '{player_name}' matched to staff: {match.name} ({match.rank})")
        else:
            print(f"✗ '{player_name}' - no match found")


if __name__ == '__main__':
    print("=" * 50)
    print("Staff Name Matching Test Suite")
    print("=" * 50)
    print()
    
    # Run tests
    test_normalize_name()
    test_staff_matching()
    
    print("\n" + "=" * 50)
    print("Test suite completed!")
    print("=" * 50)
