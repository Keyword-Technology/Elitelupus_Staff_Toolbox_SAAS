"""
Standalone test of CSV parsing (no Django needed)
"""
import csv
from io import StringIO

import requests

SHEET_ID = '1SSn3GXggr84dOYfQZzeHiRI0B1vaDkGynUyYHWfXIBo'
SHEET_NAME = 'Staff Roster'  # Changed from "Roster" to "Staff Roster"

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
    print(f"Headers (first 10 columns): {headers[:10]}")
    
    # Expected columns from "Staff Roster" Google Sheet:
    # Column 0: Empty, Column 1: Number (99), Column 2: Rank, Column 3: Timezone, 
    # Column 4: Time, Column 5: Name, Column 6: SteamID, Column 7: DiscordID, Column 8: Discord Tag
    for row_num, row in enumerate(reader, 2):
        print(f"\nRow {row_num}: {len(row)} columns")
        if len(row) >= 9:
            print(f"  [0] Empty: '{row[0]}'")
            print(f"  [1] Number: '{row[1]}'")
            print(f"  [2] Rank: '{row[2]}'")
            print(f"  [3] Timezone: '{row[3]}'")
            print(f"  [4] Time: '{row[4]}'")
            print(f"  [5] Name: '{row[5]}'")
            print(f"  [6] SteamID: '{row[6]}'")
            print(f"  [7] DiscordID: '{row[7]}'")
            print(f"  [8] Discord Tag: '{row[8]}'")
            
            # Check if row has a valid rank (column 2)
            if row[2].strip():
                rank = row[2].strip().replace('"', '')
                
                # Skip header rows
                if rank.lower() not in ['rank', 'staff rank', 'rank manager', '']:
                    staff_data = {
                        'rank': rank,
                        'timezone': row[3].strip().replace('"', '').replace('Timezone ', ''),
                        'active_time': row[4].strip().replace('"', '').replace('Time ', ''),
                        'name': row[5].strip().replace('"', '').replace('Name ', ''),
                        'steam_id': row[6].strip().replace('"', '').replace('SteamID ', ''),
                        'discord_id': row[7].strip().replace('"', '').replace('DiscordID ', ''),
                        'discord_tag': row[8].strip().replace('"', '').replace('Discord Tag ', ''),
                    }
                    
                    # Only add if we have at least a name and one identifier
                    if staff_data['name'] and (staff_data['steam_id'] or staff_data['discord_id']):
                        staff_list.append(staff_data)
                        print(f"  ✓ Added: {staff_data['name']} ({staff_data['rank']})")
                    else:
                        print(f"  ✗ Skipped (missing name or identifiers)")
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
