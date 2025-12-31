import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.staff.services import StaffSyncService

print("=" * 60)
print("TESTING GOOGLE SHEETS SYNC")
print("=" * 60)

service = StaffSyncService()
print(f"\nGoogle Sheets ID: {service.sheet_id}")
print(f"Sheet Name: {service.SHEET_NAME}")
print(f"Sheet URL: {service.sheet_url}")

print("\n" + "=" * 60)
print("FETCHING CSV DATA FROM GOOGLE SHEETS")
print("=" * 60)

try:
    csv_content = service.fetch_sheet_data()
    print(f"✓ Successfully fetched CSV data ({len(csv_content)} bytes)")
    
    # Show first few lines
    lines = csv_content.split('\n')[:3]
    print(f"\nFirst 3 lines of CSV:")
    for i, line in enumerate(lines, 1):
        print(f"  Line {i}: {line[:100]}{'...' if len(line) > 100 else ''}")
    
except Exception as e:
    print(f"✗ Error fetching CSV: {e}")
    exit(1)

print("\n" + "=" * 60)
print("PARSING CSV DATA")
print("=" * 60)

try:
    staff_data = service.parse_csv_data(csv_content)
    print(f"✓ Successfully parsed {len(staff_data)} staff members")
    
    if staff_data:
        print("\nParsed staff members:")
        for i, staff in enumerate(staff_data, 1):
            print(f"{i:2}. {staff['name']:20} - {staff['rank']:20} - {staff['steam_id']}")
    else:
        print("\n⚠ No staff members parsed!")
        
except Exception as e:
    print(f"✗ Error parsing CSV: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 60)
print("RUNNING FULL SYNC")
print("=" * 60)

try:
    result = service.sync_staff_roster()
    print(f"✓ Sync completed successfully")
    
    from apps.staff.models import Staff, StaffRoster
    
    active_roster = StaffRoster.objects.filter(is_active=True).count()
    total_staff = Staff.objects.count()
    
    print(f"\nDatabase state:")
    print(f"  Active roster entries: {active_roster}")
    print(f"  Total staff records: {total_staff}")
    
    if active_roster >= 24:
        print(f"\n✓ SUCCESS: Loaded {active_roster} staff members (expected 24+)")
    else:
        print(f"\n⚠ WARNING: Only loaded {active_roster} staff members (expected 24+)")
        
except Exception as e:
    print(f"✗ Error during sync: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
