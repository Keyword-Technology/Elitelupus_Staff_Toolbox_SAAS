import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import csv
from io import StringIO

from apps.staff.services import StaffSyncService

service = StaffSyncService()
csv_content = service.fetch_sheet_data()

print('CSV Length:', len(csv_content) if csv_content else 0)
print('First 1000 chars:')
print(repr(csv_content[:1000]) if csv_content else 'No data')
print('---')

# Debug: Show first 5 rows
if csv_content:
    reader = csv.reader(StringIO(csv_content))
    for i, row in enumerate(reader):
        if i >= 5:
            break
        print(f"Row {i}: {row}")

print('---')
staff = service.parse_csv_data(csv_content)
print(f'Parsed {len(staff)} staff members')

if staff:
    for s in staff[:10]:
        print(f"  - {s['name']} ({s['rank']}): {s['steam_id']}")
