from django.urls import path
from .views import (
    ServerListView,
    ServerDetailView,
    ServerStatusView,
    RefreshServersView,
    ServerPlayersView,
    StaffDistributionView,
    ServerHistoryView,
)

urlpatterns = [
    path('', ServerListView.as_view(), name='server_list'),
    path('status/', ServerStatusView.as_view(), name='server_status'),
    path('refresh/', RefreshServersView.as_view(), name='refresh_servers'),
    path('distribution/', StaffDistributionView.as_view(), name='staff_distribution'),
    path('<int:pk>/', ServerDetailView.as_view(), name='server_detail'),
    path('<int:pk>/players/', ServerPlayersView.as_view(), name='server_players'),
    path('<int:pk>/history/', ServerHistoryView.as_view(), name='server_history'),
]
