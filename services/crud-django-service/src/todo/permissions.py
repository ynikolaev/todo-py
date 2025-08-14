# botauth/permissions.py
from typing import Literal

from django.conf import settings
from rest_framework import exceptions, permissions

from .security import verify_hmac


# Permission class to verify HMAC for bot calls
class IsSignedBotCall(permissions.BasePermission):
    def has_permission(self, request, view):
        verify_hmac(request)
        return True


# Permission class to allow only the bot service user
class IsBotService(permissions.BasePermission):
    """Allow only the JWT-authenticated service user."""

    def has_permission(self, request, view) -> Literal[True]:
        u = getattr(request, "user", None)
        print(f"User: {u}, Username: {getattr(u, 'username', None)}")
        if not (
            u and u.is_authenticated and u.username == settings.BOT_SERVICE_USERNAME
        ):
            raise exceptions.PermissionDenied(
                "This endpoint is only accessible by the bot service user."
            )
        return True
