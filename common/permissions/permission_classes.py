from rest_framework.exceptions import ParseError
from rest_framework.permissions import BasePermission

from common.apps.organization_role.models import OrganizationPolicy
from common.apps.space_role.models import SpacePolicy


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


def has_organization_permission_access(permission):
    """
    Allows access only to users who have specific organization permissions.
    """

    class HasPermissionAccess(BasePermission):
        __permission = permission

        def has_permission(self, request, view):
            policies = OrganizationPolicy.objects.filter(
                organizationrole__organization_role_user__organization_user_id=request.user.id,
            ).distinct()
            return self.__permission in [
                policy_permission
                for policy in policies
                for policy_permission in policy.permissions
            ]

    return HasPermissionAccess
