from common.apps.refresh_tokens.models import (
    RefreshToken,
    RefreshTokenFamilyStatus,
    RefreshTokenStatus,
)
from common.apps.refresh_tokens.services import create_refresh_token
from django.conf import settings
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from rest_framework_simplejwt.settings import api_settings

JWTRefreshToken = import_string(settings.REFRESH_TOKEN_CLASS)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    token_class = JWTRefreshToken

    def validate(self, attrs):
        data = super().validate(attrs)

        refresh_token, access_token = create_refresh_token(self.user)

        data["refresh"] = str(refresh_token)
        data["access"] = str(access_token)

        return data


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    token_class = JWTRefreshToken

    def validate(self, attrs):
        refresh = self.token_class(attrs["refresh"])

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
