from django.contrib import admin
from .models import RuleCategory, Rule, JobAction


@admin.register(RuleCategory)
class RuleCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'is_active']
    ordering = ['order', 'name']


@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = ['code', 'title', 'category', 'order', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['code', 'title', 'content']
    ordering = ['category', 'order', 'code']


@admin.register(JobAction)
class JobActionAdmin(admin.ModelAdmin):
    list_display = ['job_name', 'category', 'can_raid', 'can_steal', 
                   'can_mug', 'can_kidnap', 'can_base', 'can_have_printers']
    list_filter = ['category', 'can_raid', 'can_steal', 'can_mug']
    search_fields = ['job_name']
    ordering = ['category', 'order', 'job_name']
