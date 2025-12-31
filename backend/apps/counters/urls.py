from django.urls import re_path

from .views import (CounterHistoryView, CounterStatsView, CounterUpdateView,
                    LeaderboardView, MyCountersView)

urlpatterns = [
    re_path(r'^$', MyCountersView.as_view(), name='my_counters'),
    re_path(r'^update/(?P<counter_type>[^/]+)/?$', CounterUpdateView.as_view(), name='counter_update'),
    re_path(r'^stats/?$', CounterStatsView.as_view(), name='counter_stats'),
    re_path(r'^history/?$', CounterHistoryView.as_view(), name='counter_history'),
    re_path(r'^leaderboard/?$', LeaderboardView.as_view(), name='leaderboard'),
]
