from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ParseError
from rest_framework.permissions import BasePermission

from common.apps.space_role.models import SpacePolicy

User = get_user_model()


def is_method(methods):
    class IsMethodRequest(BasePermission):
        def has_permission(self, request, view):
            if isinstance(methods, str):
                return request.method == methods
            elif isinstance(methods, list) or isinstance(methods, tuple):
                return request.method in methods
            return False

    return IsMethodRequest


def has_space_permission_access(permission):
    """
    Allows access only to users who have specific space permissions.
    """

    class HasPermissionAccess(BasePermission):
        __permission = permission

        def has_permission(self, request, view):
            space_slug_name = request.headers.get("X-Space", None)
            if space_slug_name is None:
                raise ParseError("X-Space header is required")

            policies = SpacePolicy.objects.filter(
                spacerole__space__slug_name=space_slug_name,
                spacerole__space_role_user__organization_user_id=request.user.id,
            ).distinct()
            return self.__permission in [
                policy_permission
                for policy in policies
                for policy_permission in policy.permissions
            ]

    return HasPermissionAccess

class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        try:
            user = User.objects.get(id=request.user.id)
            return user.organization_users.is_owner
        except User.DoesNotExist:
            return False
        return super().has_object_permission(request, view, obj)


class HasAPIKey(BasePermission):
    def has_permission(self, request, view):
        spacedf_key = request.headers.get("x-api-key", None)
        # TODO: need model for this
        return settings.ROOT_API_KEY == spacedf_key
