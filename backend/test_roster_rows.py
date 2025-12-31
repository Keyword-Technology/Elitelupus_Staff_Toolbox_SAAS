import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import csv
from io import StringIO

import requests

# The sheet ID from the URL the user provided
SHEET_ID = "1SSn3GXggr84dOYfQZzeHiRI0B1vaDkGynUyYHWfXIBo"
SHEET_NAME = "Staff Roster"
SHEET_GID = "160655123"

print("=" * 60)
print("TESTING GOOGLE SHEET ROW COUNT")
print("=" * 60)
print(f"\nSheet ID: {SHEET_ID}")
print(f"Sheet Name: {SHEET_NAME}")
print(f"GID: {SHEET_GID}")

# Try with sheet name
url_with_name = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"
print(f"\nFetching from: {url_with_name}")

try:
    response = requests.get(url_with_name, timeout=30)
    response.raise_for_status()
    csv_content = response.content.decode('utf-8')
    print(f"✓ Successfully fetched CSV data ({len(csv_content)} bytes)")
except Exception as e:
    print(f"✗ Error fetching with sheet name: {e}")
    
    # Try with GID instead
    url_with_gid = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={SHEET_GID}"
    print(f"\nTrying with GID: {url_with_gid}")
    
    try:
        response = requests.get(url_with_gid, timeout=30)
        response.raise_for_status()
        csv_content = response.content.decode('utf-8')
        print(f"✓ Successfully fetched CSV data ({len(csv_content)} bytes)")
    except Exception as e:
        print(f"✗ Error fetching with GID: {e}")
        exit(1)

# Parse the CSV
print("\n" + "=" * 60)
print("ANALYZING CSV STRUCTURE")
print("=" * 60)

reader = csv.reader(StringIO(csv_content))
all_rows = list(reader)

print(f"\nTotal rows in CSV: {len(all_rows)}")

# Find header row
header_row_index = None
for i, row in enumerate(all_rows):
    row_str = ' '.join([str(cell).lower() for cell in row if cell])
    if 'rank' in row_str and 'name' in row_str and 'steam' in row_str:
        header_row_index = i
        print(f"Header row found at index: {i} (row {i+1})")
        print(f"Headers: {row}")
        break

if header_row_index is None:
    print("⚠ Could not find header row")
else:
    # Count data rows after header
    data_rows = []
    for i in range(header_row_index + 1, len(all_rows)):
        row = all_rows[i]
        # Skip empty rows
        if any(cell.strip() for cell in row if cell):
            data_rows.append(row)
    
    print(f"\nData rows after header: {len(data_rows)}")
    
    # Show first few data rows
    print("\nFirst 5 data rows:")
    for i, row in enumerate(data_rows[:5], 1):
        # Extract just the relevant columns
        row_preview = [cell[:30] for cell in row if cell.strip()][:7]  # First 7 non-empty columns
        print(f"  {i}. {row_preview}")
    
    if len(data_rows) >= 24:
        print(f"\n✓ SUCCESS: Found {len(data_rows)} staff rows (expected 24+)")
    else:
        print(f"\n⚠ WARNING: Only found {len(data_rows)} staff rows (expected 24)")

print("\n" + "=" * 60)
print("ROW COUNT TEST COMPLETE")
print("=" * 60)
