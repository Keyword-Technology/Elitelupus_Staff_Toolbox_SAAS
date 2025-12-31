from django.contrib import admin

from .models import (BanExtensionTemplate, PlayerReportTemplate,
                     RefundTemplate, ResponseTemplate,
                     StaffApplicationResponse, SteamProfileHistory,
                     SteamProfileSearch, TemplateCategory, TemplateComment)


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


@admin.register(BanExtensionTemplate)
class BanExtensionTemplateAdmin(admin.ModelAdmin):
    """Admin for ban extension templates."""
    list_display = [
        'player_ign', 'ban_reason_short', 'status', 'is_active_ban',
        'submitted_by', 'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['player_ign', 'steam_id', 'steam_id_64', 'ban_reason']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    def ban_reason_short(self, obj):
        return obj.ban_reason[:50] + '...' if len(obj.ban_reason) > 50 else obj.ban_reason
    ban_reason_short.short_description = 'Ban Reason'
    
    def is_active_ban(self, obj):
        return obj.is_active_ban
    is_active_ban.boolean = True
    is_active_ban.short_description = 'Active Ban'


@admin.register(PlayerReportTemplate)
class PlayerReportTemplateAdmin(admin.ModelAdmin):
    """Admin for player report templates."""
    list_display = [
        'player_ign', 'status', 'action_taken', 'handled_by', 'created_at'
    ]
    list_filter = ['status', 'action_taken', 'created_at']
    search_fields = ['player_ign', 'steam_id', 'steam_id_64', 'report_reason']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(StaffApplicationResponse)
class StaffApplicationResponseAdmin(admin.ModelAdmin):
    """Admin for staff application responses."""
    list_display = [
        'applicant_name', 'rating', 'recommend_hire', 'reviewed_by', 'created_at'
    ]
    list_filter = ['rating', 'recommend_hire', 'created_at']
    search_fields = ['applicant_name', 'discord_username', 'steam_id_64']
    readonly_fields = ['created_at', 'updated_at', 'rating_stars']
    ordering = ['-created_at']


@admin.register(TemplateComment)
class TemplateCommentAdmin(admin.ModelAdmin):
    """Admin for template comments."""
    list_display = ['template_type', 'template_id', 'author', 'comment_preview', 'created_at']
    list_filter = ['template_type', 'created_at']
    search_fields = ['comment', 'author__username']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    def comment_preview(self, obj):
        return obj.comment[:75] + '...' if len(obj.comment) > 75 else obj.comment
    comment_preview.short_description = 'Comment'

