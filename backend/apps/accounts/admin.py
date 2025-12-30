from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        'username', 'display_name', 'email', 'role', 'role_priority',
        'is_active_staff', 'steam_id', 'discord_username', 'is_active'
    ]
    list_filter = ['role', 'is_active_staff', 'is_active', 'is_staff']
    search_fields = ['username', 'display_name', 'email', 'steam_id', 'discord_id']
    ordering = ['role_priority', 'username']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Staff Info', {
            'fields': ('display_name', 'avatar_url', 'role', 'role_priority', 
                      'is_active_staff', 'staff_since', 'timezone')
        }),
        ('Steam', {
            'fields': ('steam_id', 'steam_id_64', 'steam_profile_url', 'steam_avatar')
        }),
        ('Discord', {
            'fields': ('discord_id', 'discord_username', 'discord_discriminator', 'discord_avatar')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Staff Info', {
            'fields': ('display_name', 'role', 'is_active_staff')
        }),
    )
