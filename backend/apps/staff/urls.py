from django.urls import re_path

from .views import (BackfillLastSeenView, DeleteHistoryEventView,
                    DiscordBotStatusView, DiscordStatusSyncView,
                    FixLastSeenView, MyStaffProfileView, RecentPromotionsView,
                    RolePrioritiesView, ServerTimeLeaderboardView,
                    StaffDailyBreakdownView, StaffDetailsView,
                    StaffRosterDetailView, StaffRosterListView,
                    StaffSessionsView, StaffStatsView, StaffSyncLogListView,
                    StaffSyncView, SteamNameSyncView)

urlpatterns = [
    re_path(r'^roster/?$', StaffRosterListView.as_view(), name='staff_roster_list'),
    re_path(r'^roster/(?P<pk>\d+)/?$', StaffRosterDetailView.as_view(), name='staff_roster_detail'),
    re_path(r'^roster/(?P<pk>\d+)/details/?$', StaffDetailsView.as_view(), name='staff_details'),
    re_path(r'^roster/(?P<pk>\d+)/sessions/?$', StaffSessionsView.as_view(), name='staff_sessions'),
    re_path(r'^roster/(?P<pk>\d+)/stats/?$', StaffStatsView.as_view(), name='staff_stats'),
    re_path(r'^roster/(?P<pk>[^/]+)/daily-breakdown/?$', StaffDailyBreakdownView.as_view(), name='staff_daily_breakdown'),
    re_path(r'^sync/?$', StaffSyncView.as_view(), name='staff_sync'),
    re_path(r'^sync/logs/?$', StaffSyncLogListView.as_view(), name='staff_sync_logs'),
    re_path(r'^sync/steam-names/?$', SteamNameSyncView.as_view(), name='steam_name_sync'),
    re_path(r'^roles/?$', RolePrioritiesView.as_view(), name='role_priorities'),
    re_path(r'^me/?$', MyStaffProfileView.as_view(), name='my_staff_profile'),
    re_path(r'^discord/sync/?$', DiscordStatusSyncView.as_view(), name='discord_status_sync'),
    re_path(r'^discord/status/?$', DiscordBotStatusView.as_view(), name='discord_bot_status'),
    re_path(r'^backfill-last-seen/?$', BackfillLastSeenView.as_view(), name='backfill_last_seen'),
    re_path(r'^fix-last-seen/?$', FixLastSeenView.as_view(), name='fix_last_seen'),
    re_path(r'^server-time-leaderboard/?$', ServerTimeLeaderboardView.as_view(), name='server_time_leaderboard'),
    re_path(r'^recent-promotions/?$', RecentPromotionsView.as_view(), name='recent_promotions'),
    re_path(r'^history-event/(?P<event_id>\d+)/?$', DeleteHistoryEventView.as_view(), name='delete_history_event'),
]
