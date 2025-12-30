from django.urls import path
from .views import (
    MyCountersView,
    CounterUpdateView,
    CounterStatsView,
    CounterHistoryView,
    LeaderboardView,
)

urlpatterns = [
    path('', MyCountersView.as_view(), name='my_counters'),
    path('update/<str:counter_type>/', CounterUpdateView.as_view(), name='counter_update'),
    path('stats/', CounterStatsView.as_view(), name='counter_stats'),
    path('history/', CounterHistoryView.as_view(), name='counter_history'),
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
]
