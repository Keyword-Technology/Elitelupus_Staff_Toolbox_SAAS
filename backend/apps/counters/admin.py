from django.contrib import admin
from .models import Counter, CounterHistory, CounterSnapshot


@admin.register(Counter)
class CounterAdmin(admin.ModelAdmin):
    list_display = ['user', 'counter_type', 'count', 'period_type', 'updated_at']
    list_filter = ['counter_type', 'period_type']
    search_fields = ['user__username', 'user__display_name']
    ordering = ['-updated_at']


@admin.register(CounterHistory)
class CounterHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'counter_type', 'action', 'old_value', 'new_value', 'timestamp']
    list_filter = ['counter_type', 'action']
    search_fields = ['user__username']
    ordering = ['-timestamp']


@admin.register(CounterSnapshot)
class CounterSnapshotAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'sit_count', 'ticket_count']
    list_filter = ['date']
    search_fields = ['user__username']
    ordering = ['-date']
