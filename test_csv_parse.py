"""
Standalone test of CSV parsing (no Django needed)
"""
import csv
from io import StringIO

import requests

SHEET_ID = '1SSn3GXggr84dOYfQZzeHiRI0B1vaDkGynUyYHWfXIBo'
SHEET_NAME = 'Roster'

def fetch_sheet_data():
    """Fetch data from Google Sheets as CSV."""
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.content.decode('utf-8')

def parse_csv_data(csv_content):
    """Parse CSV content into list of dictionaries."""
    staff_list = []
    reader = csv.reader(StringIO(csv_content))
    
    # Skip header row
    headers = next(reader, None)
    print(f"Headers: {headers}")
    
    # Expected columns from Google Sheet:
    # Column 0: Empty, Column 1: Rank, Column 2: Timezone, Column 3: Time, 
    # Column 4: Name, Column 5: SteamID, Column 6: DiscordID, Column 7: Discord Tag
    for row_num, row in enumerate(reader, 2):
        print(f"\nRow {row_num}: {len(row)} columns")
        if len(row) >= 8:
            print(f"  [0] Empty: '{row[0]}'")
            print(f"  [1] Rank: '{row[1]}'")
            print(f"  [2] Timezone: '{row[2]}'")
            print(f"  [3] Time: '{row[3]}'")
            print(f"  [4] Name: '{row[4]}'")
            print(f"  [5] SteamID: '{row[5]}'")
            print(f"  [6] DiscordID: '{row[6]}'")
            print(f"  [7] Discord Tag: '{row[7]}'")
            
            # Check if row has a valid rank (column 1)
            if row[1].strip():
                staff_data = {
                    'rank': row[1].strip().replace('"', ''),
                    'timezone': row[2].strip().replace('"', ''),
                    'active_time': row[3].strip().replace('"', ''),
                    'name': row[4].strip().replace('"', ''),
                    'steam_id': row[5].strip().replace('"', ''),
                    'discord_id': row[6].strip().replace('"', ''),
                    'discord_tag': row[7].strip().replace('"', ''),
                }
                
                # Skip header rows
                if staff_data['rank'].lower() not in ['rank', 'staff rank', '']:
                    staff_list.append(staff_data)
                    print(f"  ✓ Added: {staff_data['name']} ({staff_data['rank']})")
                else:
                    print(f"  ✗ Skipped (header row)")
            else:
                print(f"  ✗ Skipped (empty rank)")
        else:
            print(f"  ✗ Skipped (insufficient columns)")
        
        if row_num > 10:  # Only show first 10 rows
            print(f"\n... (showing first 10 rows only)")
            break
    
    return staff_list

def main():
    print("=" * 80)
    print("Testing CSV Parsing")
    print("=" * 80)
    
    print("\nFetching CSV data...")
    csv_content = fetch_sheet_data()
    print(f"✓ Fetched {len(csv_content)} characters")
    
    print("\n" + "=" * 80)
    print("Parsing CSV data...")
    print("=" * 80)
    staff_list = parse_csv_data(csv_content)
    
    print("\n" + "=" * 80)
    print(f"✓ Successfully parsed {len(staff_list)} staff members")
    print("=" * 80)
    
    if staff_list:
        print("\nFirst 5 staff members:")
        for i, staff in enumerate(staff_list[:5], 1):
            print(f"  {i}. {staff['name']} ({staff['rank']}) - {staff['steam_id']}")

if __name__ == '__main__':
    main()
