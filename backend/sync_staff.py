#!/usr/bin/env python
"""
Quick script to sync staff roster from Google Sheets.
Usage: python sync_staff.py
"""
import os

import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.staff.services import StaffSyncService

if __name__ == '__main__':
    print("Starting staff roster sync...")
    service = StaffSyncService()
    try:
        result = service.sync_staff_roster()
        print("✓ Sync completed successfully!")
        print(f"  - Records synced: {result.records_synced if result else 'N/A'}")
        print(f"  - Records added: {result.records_added if result else 'N/A'}")
        print(f"  - Records updated: {result.records_updated if result else 'N/A'}")
    except Exception as e:
        print(f"✗ Sync failed: {e}")
