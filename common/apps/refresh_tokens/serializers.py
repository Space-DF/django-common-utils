import logging

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions, serializers
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from rest_framework_simplejwt.settings import api_settings

from common.apps.refresh_tokens.models import (
    RefreshToken,
    RefreshTokenFamilyStatus,
    RefreshTokenStatus,
)
from common.apps.refresh_tokens.services import create_refresh_token
from common.utils.social_provider import SocialProvider

JWTRefreshToken = import_string(settings.REFRESH_TOKEN_CLASS)
User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    token_class = JWTRefreshToken

    def authenticate(self, email: str, password: str):
        self.user = None
        try:
            self.user = User.objects.get(
                email__iexact=email,
                providers__contains=[SocialProvider.NONE_PROVIDER],
            )
        except User.DoesNotExist as e:
            logging.exception(e)
        if self.user:
            authenticate_kwargs = {
                self.username_field: email,
                "password": password,
            }
            self.user = authenticate(**authenticate_kwargs)

    def validate(self, attrs):
        data = {}
        self.authenticate(email=attrs["email"], password=attrs["password"])
        if not self.user:
            raise exceptions.AuthenticationFailed(
                self.error_messages["no_active_account"],
                "no_active_account",
            )
        tenant = None
        if hasattr(self.context["request"], "tenant"):
            tenant = self.context["request"].tenant
        refresh_token, access_token = create_refresh_token(self.user, issuer=tenant)
        data["refresh"] = str(refresh_token)
        data["access"] = str(access_token)

        return data


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    token_class = JWTRefreshToken

    def validate(self, attrs):
        refresh = self.token_class(attrs["refresh"])

        if hasattr(self.context["request"], "tenant"):
            refresh.check_iss()
        refresh_token_obj = (
            RefreshToken.objects.filter(jti=refresh.payload[api_settings.JTI_CLAIM])
            .select_related("family")
            .first()
        )

        if not refresh_token_obj:
            raise TokenError(_("Refresh token is not found"))

        if refresh_token_obj.status != RefreshTokenStatus.New:
            refresh_token_obj.family.status = RefreshTokenFamilyStatus.Inactive
            refresh_token_obj.family.save()
            raise TokenError(_("Refresh token is inactive"))

        if refresh_token_obj.family.status != RefreshTokenFamilyStatus.Active:
            raise TokenError(_("Refresh token is inactive"))

        data = {"access": str(refresh.access_token)}

        refresh.set_jti()
        refresh.set_exp()
        refresh.set_iat()

        RefreshToken(
            jti=refresh.payload[api_settings.JTI_CLAIM],
            family=refresh_token_obj.family,
            parent=refresh_token_obj,
        ).save()

        refresh_token_obj.status = RefreshTokenStatus.Used
        refresh_token_obj.save()

        data["refresh"] = str(refresh)

        return data


class TokenPairSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
