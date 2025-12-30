from django.contrib import admin
from .models import SystemSetting, ManagedServer, SettingAuditLog


@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ['key', 'category', 'setting_type', 'is_sensitive', 'is_active', 'updated_at']
    list_filter = ['category', 'setting_type', 'is_sensitive', 'is_active']
    search_fields = ['key', 'description']
    ordering = ['category', 'key']
    
    fieldsets = (
        (None, {
            'fields': ('key', 'value', 'setting_type', 'category')
        }),
        ('Options', {
            'fields': ('description', 'is_sensitive', 'is_active')
        }),
        ('Metadata', {
            'fields': ('updated_by',),
            'classes': ('collapse',)
        }),
    )


@admin.register(ManagedServer)
class ManagedServerAdmin(admin.ModelAdmin):
    list_display = ['name', 'ip_address', 'port', 'is_active', 'display_order', 'updated_at']
    list_filter = ['is_active']
    search_fields = ['name', 'ip_address', 'description']
    ordering = ['display_order', 'name']


@admin.register(SettingAuditLog)
class SettingAuditLogAdmin(admin.ModelAdmin):
    list_display = ['setting', 'user', 'changed_at', 'ip_address']
    list_filter = ['changed_at']
    search_fields = ['setting__key', 'user__username']
    ordering = ['-changed_at']
    readonly_fields = ['setting', 'user', 'old_value', 'new_value', 'changed_at', 'ip_address']
