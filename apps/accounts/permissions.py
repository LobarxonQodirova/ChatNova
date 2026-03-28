"""
Custom permissions for the accounts app.
"""
from rest_framework.permissions import BasePermission


class IsAccountOwner(BasePermission):
    """Only allows users to modify their own account."""

    def has_object_permission(self, request, view, obj):
        return obj == request.user or request.user.is_staff


class IsVerifiedUser(BasePermission):
    """Only allows verified users to access the view."""

    message = "Your account must be verified to perform this action."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_verified


class IsNotBlocked(BasePermission):
    """Denies access if the request user has been blocked by the target user."""

    message = "You have been blocked by this user."

    def has_object_permission(self, request, view, obj):
        from apps.contacts.models import BlockedUser

        target_user = getattr(obj, "user", obj)
        return not BlockedUser.objects.filter(
            user=target_user, blocked_user=request.user
        ).exists()
