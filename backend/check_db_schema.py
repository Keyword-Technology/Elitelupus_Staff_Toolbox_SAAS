import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

# Use raw SQL since models don't match schema
with connection.cursor() as cursor:
    # Check StaffRoster schema
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'staff_staffroster'
        ORDER BY ordinal_position;
    """)
    print("=== StaffRoster Schema ===")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")
    
    # Check ServerSession schema
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'staff_serversession'
        ORDER BY ordinal_position;
    """)
    print("\n=== ServerSession Schema ===")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")
    
    # Check StaffHistoryEvent schema
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'staff_staffhistoryevent'
        ORDER BY ordinal_position;
    """)
    print("\n=== StaffHistoryEvent Schema ===")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")
    
    # Check Staff schema
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'staff_staff'
        ORDER BY ordinal_position;
    """)
    print("\n=== Staff Schema ===")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")
    
    # Get mapping of StaffRoster ID to steam_id
    cursor.execute("""
        SELECT id, steam_id, name 
        FROM staff_staffroster 
        LIMIT 10;
    """)
    print("\n=== StaffRoster ID to steam_id mapping (sample) ===")
    for row in cursor.fetchall():
        print(f"  ID {row[0]}: {row[1]} ({row[2]})")
    
    # Check ServerSession staff_id values
    cursor.execute("""
        SELECT DISTINCT staff_id 
        FROM staff_serversession 
        ORDER BY staff_id 
        LIMIT 20;
    """)
    print("\n=== Distinct staff_id values in ServerSession ===")
    staff_ids = [row[0] for row in cursor.fetchall()]
    print(f"  {staff_ids}")
    
    # Check if any ServerSession.staff_id doesn't exist in StaffRoster
    cursor.execute("""
        SELECT DISTINCT ss.staff_id
        FROM staff_serversession ss
        LEFT JOIN staff_staffroster sr ON ss.staff_id = sr.id
        WHERE sr.id IS NULL
        LIMIT 20;
    """)
    orphaned = [row[0] for row in cursor.fetchall()]
    if orphaned:
        print(f"\n=== Orphaned staff_id values (no matching StaffRoster.id) ===")
        print(f"  {orphaned}")
    else:
        print("\n=== No orphaned staff_id values ===")
