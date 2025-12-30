from django.urls import path

from .views import (EnvironmentVariableListView, EnvironmentVariableUpdateView,
                    ManagedServerDetailView, ManagedServerListView,
                    SettingAuditLogListView, SyncManagedServersView,
                    SystemSettingDetailView, SystemSettingListView)

urlpatterns = [
    # Environment Variables
    path('env/', EnvironmentVariableListView.as_view(), name='env_list'),
    path('env/<str:key>/', EnvironmentVariableUpdateView.as_view(), name='env_update'),
    
    # System Settings
    path('settings/', SystemSettingListView.as_view(), name='system_settings_list'),
    path('settings/<int:pk>/', SystemSettingDetailView.as_view(), name='system_settings_detail'),
    
    # Managed Servers
    path('servers/', ManagedServerListView.as_view(), name='managed_servers_list'),
    path('servers/<int:pk>/', ManagedServerDetailView.as_view(), name='managed_servers_detail'),
    path('servers/sync/', SyncManagedServersView.as_view(), name='managed_servers_sync'),
    
    # Audit Logs
    path('audit-logs/', SettingAuditLogListView.as_view(), name='audit_logs_list'),
]
