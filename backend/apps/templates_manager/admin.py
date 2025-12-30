from django.contrib import admin
from .models import RefundTemplate, TemplateCategory, ResponseTemplate


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
