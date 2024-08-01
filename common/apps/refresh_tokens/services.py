from common.apps.refresh_tokens.models import RefreshToken, RefreshTokenFamily
from django.conf import settings
from django.utils.module_loading import import_string
from rest_framework_simplejwt.settings import api_settings

JWTRefreshToken = import_string(settings.REFRESH_TOKEN_CLASS)


def create_refresh_token(user):
    refresh = JWTRefreshToken.for_user(user)

    token_family = RefreshTokenFamily(user=user)
    token_family.save()
    RefreshToken(
        jti=refresh.payload[api_settings.JTI_CLAIM], family=token_family
    ).save()

    return refresh, refresh.access_token
