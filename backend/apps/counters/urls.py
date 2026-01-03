from django.urls import re_path

from .views import (ActiveSitView, CounterHistoryView,  # Sit Recording System
                    CounterStatsView, CounterUpdateView, LeaderboardView,
                    MyCountersView, ResetWeeklySitCounterView, SitDetailView,
                    SitListCreateView, SitNoteDeleteView,
                    SitNoteListCreateView, SitRecordingEnabledView,
                    SitRecordingUploadView, SitStatsView,
                    UserSitPreferencesView)

urlpatterns = [
    # Legacy counter endpoints (unchanged)
    re_path(r'^/?$', MyCountersView.as_view(), name='my_counters'),
    re_path(r'^update/(?P<counter_type>[^/]+)/?$', CounterUpdateView.as_view(), name='counter_update'),
    re_path(r'^stats/?$', CounterStatsView.as_view(), name='counter_stats'),
    re_path(r'^history/?$', CounterHistoryView.as_view(), name='counter_history'),
    re_path(r'^leaderboard/?$', LeaderboardView.as_view(), name='leaderboard'),
    re_path(r'^reset-weekly-sits/?$', ResetWeeklySitCounterView.as_view(), name='reset_weekly_sits'),
    
    # Sit Recording System endpoints
    re_path(r'^sits/enabled/?$', SitRecordingEnabledView.as_view(), name='sit_recording_enabled'),
    re_path(r'^sits/preferences/?$', UserSitPreferencesView.as_view(), name='sit_preferences'),
    re_path(r'^sits/stats/?$', SitStatsView.as_view(), name='sit_stats'),
    re_path(r'^sits/active/?$', ActiveSitView.as_view(), name='active_sit'),
    re_path(r'^sits/?$', SitListCreateView.as_view(), name='sit_list_create'),
    re_path(r'^sits/(?P<sit_id>[0-9a-f-]+)/?$', SitDetailView.as_view(), name='sit_detail'),
    re_path(r'^sits/(?P<sit_id>[0-9a-f-]+)/recording/?$', SitRecordingUploadView.as_view(), name='sit_recording_upload'),
    re_path(r'^sits/(?P<sit_id>[0-9a-f-]+)/notes/?$', SitNoteListCreateView.as_view(), name='sit_notes'),
    re_path(r'^sits/(?P<sit_id>[0-9a-f-]+)/notes/(?P<note_id>\d+)/?$', SitNoteDeleteView.as_view(), name='sit_note_delete'),
]
