from django.urls import re_path

from .views import (CounterQuotaView, EnvironmentVariableListView,
                    EnvironmentVariableUpdateView, ManagedServerDetailView,
                    ManagedServerListView, SettingAuditLogListView,
                    SyncManagedServersView, SystemSettingDetailView,
                    SystemSettingListView)

urlpatterns = [
    # Environment Variables
    re_path(r'^env/?$', EnvironmentVariableListView.as_view(), name='env_list'),
    re_path(r'^env/(?P<key>[^/]+)/?$', EnvironmentVariableUpdateView.as_view(), name='env_update'),
    
    # System Settings
    re_path(r'^settings/?$', SystemSettingListView.as_view(), name='system_settings_list'),
    re_path(r'^settings/(?P<pk>\d+)/?$', SystemSettingDetailView.as_view(), name='system_settings_detail'),
    
    # Counter Quotas (public endpoint)
    re_path(r'^quotas/?$', CounterQuotaView.as_view(), name='counter_quotas'),
    
    # Managed Servers
    re_path(r'^servers/?$', ManagedServerListView.as_view(), name='managed_servers_list'),
    re_path(r'^servers/(?P<pk>\d+)/?$', ManagedServerDetailView.as_view(), name='managed_servers_detail'),
    re_path(r'^servers/sync/?$', SyncManagedServersView.as_view(), name='managed_servers_sync'),
    
    # Audit Logs
    re_path(r'^audit-logs/?$', SettingAuditLogListView.as_view(), name='audit_logs_list'),
]
