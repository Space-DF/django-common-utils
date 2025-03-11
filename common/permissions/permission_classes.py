from django.conf import settings
from rest_framework.permissions import BasePermission


class HasAPIKey(BasePermission):
    def has_permission(self, request, view):
        spacedf_key = request.headers.get("x-api-key", None)
        # TODO: need model for this
        return settings.ROOT_API_KEY == spacedf_key
