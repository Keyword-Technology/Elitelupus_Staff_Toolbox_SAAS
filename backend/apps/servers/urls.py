from django.urls import re_path

from .views import (PlayerLookupView, RefreshServersView, ServerDetailView,
                    ServerHistoryView, ServerListView, ServerPlayersView,
                    ServerStatsView, ServerStatusView, StaffDistributionView)

urlpatterns = [
    re_path(r'^/?$', ServerListView.as_view(), name='server_list'),
    re_path(r'^status/?$', ServerStatusView.as_view(), name='server_status'),
    re_path(r'^refresh/?$', RefreshServersView.as_view(), name='refresh_servers'),
    re_path(r'^distribution/?$', StaffDistributionView.as_view(), name='staff_distribution'),
    re_path(r'^player-lookup/?$', PlayerLookupView.as_view(), name='player_lookup'),
    re_path(r'^(?P<pk>\d+)/?$', ServerDetailView.as_view(), name='server_detail'),
    re_path(r'^(?P<pk>\d+)/players/?$', ServerPlayersView.as_view(), name='server_players'),
    re_path(r'^(?P<pk>\d+)/history/?$', ServerHistoryView.as_view(), name='server_history'),
    re_path(r'^(?P<pk>\d+)/stats/?$', ServerStatsView.as_view(), name='server_stats'),
]
