from django.urls import path, re_path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (CustomTokenObtainPairView, LegacyStaffListView, LogoutView,
                    OAuthCallbackView, OAuthErrorView, PasswordChangeView,
                    ProfileView, RegisterView, SocialLinkStatusView,
                    StaffListView, SteamAuthCallbackView, TimezonesView,
                    UnlinkSocialAccountView, UserDetailView)

urlpatterns = [
    # JWT Authentication (with optional trailing slash)
    re_path(r'^token/?$', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    re_path(r'^token/refresh/?$', TokenRefreshView.as_view(), name='token_refresh'),
    # re_path(r'^register/?$', RegisterView.as_view(), name='register'),  # DISABLED: User registration
    re_path(r'^logout/?$', LogoutView.as_view(), name='logout'),
    
    # OAuth Callback (generates JWT tokens after social auth)
    re_path(r'^oauth/callback/?$', OAuthCallbackView.as_view(), name='oauth_callback'),
    re_path(r'^oauth/error/?$', OAuthErrorView.as_view(), name='oauth_error'),
    
    # Profile Management
    re_path(r'^profile/?$', ProfileView.as_view(), name='profile'),
    re_path(r'^password/change/?$', PasswordChangeView.as_view(), name='password_change'),
    re_path(r'^timezones/?$', TimezonesView.as_view(), name='timezones'),
    
    # Social Account Linking
    re_path(r'^social/status/?$', SocialLinkStatusView.as_view(), name='social_status'),
    re_path(r'^social/unlink/(?P<provider>[^/]+)/?$', UnlinkSocialAccountView.as_view(), name='social_unlink'),
    re_path(r'^steam/callback/?$', SteamAuthCallbackView.as_view(), name='steam_callback'),
    
    # Staff Management
    re_path(r'^staff/?$', StaffListView.as_view(), name='staff_list'),
    re_path(r'^staff/legacy/?$', LegacyStaffListView.as_view(), name='legacy_staff_list'),
    re_path(r'^users/(?P<pk>\d+)/?$', UserDetailView.as_view(), name='user_detail'),
]
