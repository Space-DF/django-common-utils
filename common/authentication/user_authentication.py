from typing import TypeVar

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.utils.translation import gettext_lazy as _
from rest_framework.authentication import BaseAuthentication
from rest_framework.request import Request
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.models import TokenUser
from rest_framework_simplejwt.settings import api_settings

AuthUser = TypeVar("AuthUser", AbstractBaseUser, TokenUser)


# TODO: replace JWTAuthentication by this on other service when ready
class UserAuthentication(BaseAuthentication):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.user_model = get_user_model()

    def authenticate(self, request: Request):
        header = self.get_header(request)
        if not header:
            return None

        user = self.get_user(header)

        if not user:
            return None
        return (user, None)

    def get_header(self, request: Request) -> bytes:
        """
        Extracts the header containing the `User Id` from the given
        request.
        """
        header = request.META.get("user-id")

        if isinstance(header, str):
            # Work around django test client oddness
            header = header.encode(header)

        return header

    def get_user(self, user_id: str) -> AuthUser:
        """
        Attempts to find and return a user using the given `User Id`.
        """
        try:
            user = self.user_model.objects.get(**{api_settings.USER_ID_FIELD: user_id})
        except self.user_model.DoesNotExist:
            raise AuthenticationFailed(_("User not found"), code="user_not_found")

        if not user.is_active:
            raise AuthenticationFailed(_("User is inactive"), code="user_inactive")

        return user
