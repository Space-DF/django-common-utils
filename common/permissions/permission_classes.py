from rest_framework.permissions import BasePermission


def is_method(methods):
    class IsMethodRequest(BasePermission):
        def has_permission(self, request, view):
            if isinstance(methods, str):
                return request.method == methods
            elif isinstance(methods, list) or isinstance(methods, tuple):
                return request.method in methods
            return False

    return IsMethodRequest
