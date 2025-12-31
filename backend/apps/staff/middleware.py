"""Middleware for tracking staff activity in the application."""
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

from .models import StaffRoster


class StaffActivityMiddleware(MiddlewareMixin):
    """Track when staff members are active in the application."""
    
    def process_request(self, request):
        """Update last_seen timestamp for authenticated staff users."""
        if request.user.is_authenticated:
            # Try to find staff roster entry for this user
            try:
                # Find by linked user account
                roster = StaffRoster.objects.filter(
                    user=request.user,
                    is_active=True
                ).first()
                
                # If not found by user, try by steam_id or discord_id
                if not roster and hasattr(request.user, 'steam_id') and request.user.steam_id:
                    roster = StaffRoster.objects.filter(
                        steam_id=request.user.steam_id,
                        is_active=True
                    ).first()
                
                if not roster and hasattr(request.user, 'discord_id') and request.user.discord_id:
                    roster = StaffRoster.objects.filter(
                        discord_id=request.user.discord_id,
                        is_active=True
                    ).first()
                
                # Update activity timestamp
                if roster:
                    roster.last_seen = timezone.now()
                    roster.is_active_in_app = True
                    roster.save(update_fields=['last_seen', 'is_active_in_app'])
                    
            except Exception:
                # Silently fail - don't interrupt request processing
                pass
        
        return None
