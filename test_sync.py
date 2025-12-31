"""
Quick test script for staff roster sync
"""
import os
import sys

import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import logging

from apps.staff.models import StaffRoster
from apps.staff.services import StaffSyncService

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    print("=" * 80)
    print("Testing Staff Roster Sync")
    print("=" * 80)
    
    # Check current state
    current_count = StaffRoster.objects.count()
    print(f"\nCurrent roster count: {current_count}")
    
    # Test fetching data
    service = StaffSyncService()
    print(f"\nFetching data from: {service.sheet_url}")
    
    try:
        csv_content = service.fetch_sheet_data()
        print(f"✓ Successfully fetched {len(csv_content)} characters of CSV data")
        
        # Parse CSV
        staff_data = service.parse_csv_data(csv_content)
        print(f"✓ Parsed {len(staff_data)} staff members from CSV")
        
        if staff_data:
            print("\nFirst 3 staff members:")
            for i, staff in enumerate(staff_data[:3], 1):
                print(f"  {i}. {staff['name']} ({staff['rank']}) - SteamID: {staff['steam_id']}")
        
        # Perform sync
        print("\n" + "=" * 80)
        print("Performing sync...")
        print("=" * 80)
        log = service.sync_staff_roster()
        
        print(f"\n✓ Sync completed successfully!")
        print(f"  - Records synced: {log.records_synced}")
        print(f"  - Records added: {log.records_added}")
        print(f"  - Records updated: {log.records_updated}")
        print(f"  - Records removed: {log.records_removed}")
        
        # Show final count
        final_count = StaffRoster.objects.filter(is_active=True).count()
        print(f"\nFinal active roster count: {final_count}")
        
        # Show sample records
        print("\nSample records from database:")
        for staff in StaffRoster.objects.filter(is_active=True)[:5]:
            print(f"  - {staff.name} ({staff.rank}) - {staff.steam_id}")
        
    except Exception as e:
        print(f"\n✗ Error occurred: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
