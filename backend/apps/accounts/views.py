from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone
import pytz

from .serializers import (
    UserSerializer,
    UserProfileUpdateSerializer,
    UserRegistrationSerializer,
    CustomTokenObtainPairSerializer,
    PasswordChangeSerializer,
    SocialLinkSerializer,
)
from .permissions import IsOwnerOrHigherRole

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom token view with additional user data."""
    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    """User registration endpoint."""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)


class ProfileView(generics.RetrieveUpdateAPIView):
    """Get and update user profile."""
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserProfileUpdateSerializer
        return UserSerializer

    def get_object(self):
        # Update last activity
        user = self.request.user
        user.last_activity = timezone.now()
        user.save(update_fields=['last_activity'])
        return user


class PasswordChangeView(APIView):
    """Change password for authenticated user."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {'old_password': 'Current password is incorrect.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({'message': 'Password changed successfully.'})


class TimezonesView(APIView):
    """Get list of available timezones."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({
            'timezones': pytz.common_timezones
        })


class SocialLinkStatusView(APIView):
    """Get status of linked social accounts."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'steam_linked': bool(user.steam_id),
            'steam_id': user.steam_id,
            'steam_profile_url': user.steam_profile_url,
            'discord_linked': bool(user.discord_id),
            'discord_id': user.discord_id,
            'discord_username': user.discord_username,
        })


class UnlinkSocialAccountView(APIView):
    """Unlink a social account from the user."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, provider):
        user = request.user
        
        if provider == 'steam':
            user.steam_id = None
            user.steam_id_64 = None
            user.steam_profile_url = None
            user.steam_avatar = None
        elif provider == 'discord':
            user.discord_id = None
            user.discord_username = None
            user.discord_discriminator = None
            user.discord_avatar = None
        else:
            return Response(
                {'error': 'Invalid provider'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.save()
        return Response({'message': f'{provider.title()} account unlinked successfully.'})


class SteamAuthCallbackView(APIView):
    """Handle Steam OAuth callback and generate JWT tokens."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        user = request.user
        if user.is_authenticated:
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        return Response(
            {'error': 'Authentication failed'},
            status=status.HTTP_401_UNAUTHORIZED
        )


class StaffListView(generics.ListAPIView):
    """List all staff members."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(
            is_active_staff=True
        ).order_by('role_priority', 'username')


class UserDetailView(generics.RetrieveUpdateAPIView):
    """Get or update a specific user (for admins)."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrHigherRole]
    queryset = User.objects.all()


class LogoutView(APIView):
    """Logout and blacklist the refresh token."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({'message': 'Logged out successfully.'})
        except Exception:
            return Response(
                {'error': 'Invalid token'},
                status=status.HTTP_400_BAD_REQUEST
            )
