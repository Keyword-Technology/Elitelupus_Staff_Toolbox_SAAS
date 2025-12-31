from django.contrib import admin

from .models import (RefundTemplate, ResponseTemplate, SteamProfileHistory,
                     SteamProfileSearch, TemplateCategory)


@admin.register(SteamProfileSearch)
class SteamProfileSearchAdmin(admin.ModelAdmin):
    """Admin for Steam profile search tracking."""
    list_display = [
        'steam_id_64', 'persona_name', 'search_count',
        'vac_bans', 'game_bans', 'last_searched_at', 'last_searched_by'
    ]
    list_filter = ['vac_bans', 'game_bans', 'community_banned', 'is_private']
    search_fields = ['steam_id_64', 'steam_id', 'persona_name']
    readonly_fields = [
        'search_count', 'first_searched_at', 'last_searched_at',
        'last_searched_by'
    ]
    ordering = ['-search_count', '-last_searched_at']
    
    fieldsets = (
        ('Steam IDs', {
            'fields': ('steam_id_64', 'steam_id')
        }),
        ('Profile Information', {
            'fields': (
                'persona_name', 'real_name', 'profile_url', 
                'avatar_url', 'profile_state', 'location'
            )
        }),
        ('Account Status', {
            'fields': (
                'account_created', 'is_private', 'is_limited', 'level'
            )
        }),
        ('Bans & Restrictions', {
            'fields': (
                'vac_bans', 'game_bans', 'days_since_last_ban',
                'community_banned', 'trade_ban'
            )
        }),
        ('Search Tracking', {
            'fields': (
                'search_count', 'first_searched_at', 'last_searched_at',
                'last_searched_by'
            )
        }),
    )


@admin.register(SteamProfileHistory)
class SteamProfileHistoryAdmin(admin.ModelAdmin):
    """Admin for Steam profile history tracking."""
    list_display = [
        'search', 'searched_at', 'searched_by', 'persona_name',
        'vac_bans', 'game_bans', 'has_changes'
    ]
    list_filter = ['searched_at', 'vac_bans', 'game_bans']
    search_fields = ['search__steam_id_64', 'search__persona_name', 'persona_name']
    readonly_fields = ['searched_at', 'changes_detected']
    ordering = ['-searched_at']
    
    def has_changes(self, obj):
        return bool(obj.changes_detected)
    has_changes.boolean = True
    has_changes.short_description = 'Changes Detected'


@admin.register(RefundTemplate)
class RefundTemplateAdmin(admin.ModelAdmin):
    list_display = ['ticket_number', 'player_ign', 'status', 'created_by', 'created_at']
    list_filter = ['status', 'server']
    search_fields = ['ticket_number', 'player_ign', 'steam_id']
    ordering = ['-created_at']


@admin.register(TemplateCategory)
class TemplateCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'is_active']
    ordering = ['order', 'name']


@admin.register(ResponseTemplate)
class ResponseTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_active', 'created_by', 'created_at']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'content']
    ordering = ['category', 'name']
