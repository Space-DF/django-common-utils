from django.conf import settings
from django.core.cache import cache
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission


class HasAPIKey(BasePermission):
    def has_permission(self, request, view):
        spacedf_key = request.headers.get("x-api-key", None)
        # TODO: need model for this
        return settings.ROOT_API_KEY == spacedf_key


class HasChangePermission(BasePermission):
    def has_permission(self, request, view):
        user_id = request.headers.get("X-User-ID", None)
        data = cache.get(f"space_permissions_{user_id}")
        if not data:
            raise AuthenticationFailed("Permission changed. Please refresh token.")
        return True
