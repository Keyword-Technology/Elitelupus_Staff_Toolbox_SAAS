from django.contrib import admin
from .models import StaffRoster, StaffSyncLog


@admin.register(StaffRoster)
class StaffRosterAdmin(admin.ModelAdmin):
    list_display = ['name', 'rank', 'timezone', 'steam_id', 'discord_tag', 'is_active', 'user']
    list_filter = ['rank', 'is_active', 'timezone']
    search_fields = ['name', 'steam_id', 'discord_id', 'discord_tag']
    ordering = ['rank', 'name']
    readonly_fields = ['last_synced']


@admin.register(StaffSyncLog)
class StaffSyncLogAdmin(admin.ModelAdmin):
    list_display = ['synced_at', 'success', 'records_synced', 'records_added', 
                   'records_updated', 'records_removed']
    list_filter = ['success']
    ordering = ['-synced_at']
