from rest_framework import permissions


class IsOwnerOrHigherRole(permissions.BasePermission):
    """
    Custom permission to only allow users to edit their own profile
    or users with higher role priority to edit others.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the user themselves
        # or to users with higher role priority
        return (
            obj == request.user or 
            request.user.role_priority < obj.role_priority
        )


class IsStaffMember(permissions.BasePermission):
    """Permission check for active staff members."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            request.user.is_active_staff
        )


class HasMinimumRole(permissions.BasePermission):
    """
    Permission check for minimum role requirement.
    Set required_role_priority on the view.
    """
    
    def has_permission(self, request, view):
        required_priority = getattr(view, 'required_role_priority', 999)
        return (
            request.user.is_authenticated and 
            request.user.role_priority <= required_priority
        )


class IsSysAdmin(permissions.BasePermission):
    """Permission check for system administrators."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            request.user.role == 'SYSADMIN'
        )


class IsManager(permissions.BasePermission):
    """Permission check for managers and above."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            request.user.role_priority <= 10  # Manager priority
        )


class IsStaffManager(permissions.BasePermission):
    """Permission check for staff managers and above."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            request.user.role_priority <= 20  # Staff Manager priority
        )


class IsAdmin(permissions.BasePermission):
    """Permission check for admins and above."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            request.user.role_priority <= 70  # Admin priority
        )


class IsModerator(permissions.BasePermission):
    """Permission check for moderators and above."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            request.user.role_priority <= 90  # Moderator priority
        )
