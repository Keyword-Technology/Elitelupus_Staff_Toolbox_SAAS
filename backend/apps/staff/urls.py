from django.urls import path

from .views import (DiscordBotStatusView, DiscordStatusSyncView,
                    MyStaffProfileView, RolePrioritiesView,
                    StaffRosterDetailView, StaffRosterListView,
                    StaffSyncLogListView, StaffSyncView)

urlpatterns = [
    path('roster/', StaffRosterListView.as_view(), name='staff_roster_list'),
    path('roster/<int:pk>/', StaffRosterDetailView.as_view(), name='staff_roster_detail'),
    path('sync/', StaffSyncView.as_view(), name='staff_sync'),
    path('sync/logs/', StaffSyncLogListView.as_view(), name='staff_sync_logs'),
    path('roles/', RolePrioritiesView.as_view(), name='role_priorities'),
    path('me/', MyStaffProfileView.as_view(), name='my_staff_profile'),
    path('discord/sync/', DiscordStatusSyncView.as_view(), name='discord_status_sync'),
    path('discord/status/', DiscordBotStatusView.as_view(), name='discord_bot_status'),
]
