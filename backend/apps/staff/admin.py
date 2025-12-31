from django.contrib import admin
from .models import Staff, StaffRoster, StaffSyncLog, StaffHistoryEvent, ServerSession


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ['steam_id', 'name', 'current_role', 'staff_status', 'user', 'first_joined']
    list_filter = ['staff_status', 'current_role']
    search_fields = ['steam_id', 'name', 'discord_id', 'discord_tag']
    ordering = ['current_role_priority', 'name']
    readonly_fields = ['first_joined', 'last_seen']


@admin.register(StaffRoster)
class StaffRosterAdmin(admin.ModelAdmin):
    list_display = ['staff', 'rank', 'timezone', 'is_active', 'last_synced']
    list_filter = ['rank', 'is_active', 'timezone']
    search_fields = ['staff__name', 'staff__steam_id', 'staff__discord_id']
    ordering = ['rank_priority', 'staff__name']
    readonly_fields = ['last_synced']


@admin.register(StaffSyncLog)
class StaffSyncLogAdmin(admin.ModelAdmin):
    list_display = ['synced_at', 'success', 'records_synced', 'records_added', 
                   'records_updated', 'records_removed']
    list_filter = ['success']
    ordering = ['-synced_at']


@admin.register(StaffHistoryEvent)
class StaffHistoryEventAdmin(admin.ModelAdmin):
    list_display = ['staff', 'event_type', 'old_rank', 'new_rank', 'event_date', 'auto_detected']
    list_filter = ['event_type', 'auto_detected']
    search_fields = ['staff__name', 'staff__steam_id']
    ordering = ['-event_date']


@admin.register(ServerSession)
class ServerSessionAdmin(admin.ModelAdmin):
    list_display = ['staff', 'server', 'join_time', 'leave_time', 'duration_formatted']
    list_filter = ['server']
    search_fields = ['staff__name', 'staff__steam_id', 'player_name']
    ordering = ['-join_time']
