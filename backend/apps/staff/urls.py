from django.urls import path
from .views import (
    StaffRosterListView,
    StaffRosterDetailView,
    StaffSyncView,
    StaffSyncLogListView,
    RolePrioritiesView,
    MyStaffProfileView,
)

urlpatterns = [
    path('roster/', StaffRosterListView.as_view(), name='staff_roster_list'),
    path('roster/<int:pk>/', StaffRosterDetailView.as_view(), name='staff_roster_detail'),
    path('sync/', StaffSyncView.as_view(), name='staff_sync'),
    path('sync/logs/', StaffSyncLogListView.as_view(), name='staff_sync_logs'),
    path('roles/', RolePrioritiesView.as_view(), name='role_priorities'),
    path('me/', MyStaffProfileView.as_view(), name='my_staff_profile'),
]
