from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    CustomTokenObtainPairView,
    RegisterView,
    ProfileView,
    PasswordChangeView,
    TimezonesView,
    SocialLinkStatusView,
    UnlinkSocialAccountView,
    SteamAuthCallbackView,
    StaffListView,
    UserDetailView,
    LogoutView,
    OAuthCallbackView,
)

urlpatterns = [
    # JWT Authentication
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # OAuth Callback (generates JWT tokens after social auth)
    path('oauth/callback/', OAuthCallbackView.as_view(), name='oauth_callback'),
    
    # Profile Management
    path('profile/', ProfileView.as_view(), name='profile'),
    path('password/change/', PasswordChangeView.as_view(), name='password_change'),
    path('timezones/', TimezonesView.as_view(), name='timezones'),
    
    # Social Account Linking
    path('social/status/', SocialLinkStatusView.as_view(), name='social_status'),
    path('social/unlink/<str:provider>/', UnlinkSocialAccountView.as_view(), name='social_unlink'),
    path('steam/callback/', SteamAuthCallbackView.as_view(), name='steam_callback'),
    
    # Staff Management
    path('staff/', StaffListView.as_view(), name='staff_list'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user_detail'),
]
