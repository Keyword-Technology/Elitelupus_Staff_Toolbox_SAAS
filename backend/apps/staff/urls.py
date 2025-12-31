from django.urls import re_path

from .views import (DiscordBotStatusView, DiscordStatusSyncView,
                    MyStaffProfileView, RolePrioritiesView, StaffDetailsView,
                    StaffRosterDetailView, StaffRosterListView,
                    StaffSessionsView, StaffStatsView, StaffSyncLogListView,
                    StaffSyncView)

urlpatterns = [
    re_path(r'^roster/?$', StaffRosterListView.as_view(), name='staff_roster_list'),
    re_path(r'^roster/(?P<pk>\d+)/?$', StaffRosterDetailView.as_view(), name='staff_roster_detail'),
    re_path(r'^roster/(?P<pk>\d+)/details/?$', StaffDetailsView.as_view(), name='staff_details'),
    re_path(r'^roster/(?P<pk>\d+)/sessions/?$', StaffSessionsView.as_view(), name='staff_sessions'),
    re_path(r'^roster/(?P<pk>\d+)/stats/?$', StaffStatsView.as_view(), name='staff_stats'),
    re_path(r'^sync/?$', StaffSyncView.as_view(), name='staff_sync'),
    re_path(r'^sync/logs/?$', StaffSyncLogListView.as_view(), name='staff_sync_logs'),
    re_path(r'^roles/?$', RolePrioritiesView.as_view(), name='role_priorities'),
    re_path(r'^me/?$', MyStaffProfileView.as_view(), name='my_staff_profile'),
    re_path(r'^discord/sync/?$', DiscordStatusSyncView.as_view(), name='discord_status_sync'),
    re_path(r'^discord/status/?$', DiscordBotStatusView.as_view(), name='discord_bot_status'),
]
