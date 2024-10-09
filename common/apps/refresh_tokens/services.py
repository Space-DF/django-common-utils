from django.conf import settings
from django.utils.module_loading import import_string
from rest_framework_simplejwt.settings import api_settings

from common.apps.refresh_tokens.models import RefreshToken, RefreshTokenFamily
from common.utils.subdomain import update_subdomain

JWTRefreshToken = import_string(settings.REFRESH_TOKEN_CLASS)


def create_refresh_token(user, issuer=None, **kwargs):
    refresh = JWTRefreshToken.for_user(user)
    if issuer:
        domain = update_subdomain(settings.HOST, issuer.slug_name)
        refresh.set_iss("iss", domain)
    token_family = RefreshTokenFamily(user=user)
    token_family.save()
    RefreshToken(
        jti=refresh.payload[api_settings.JTI_CLAIM], family=token_family
    ).save()

    return refresh, refresh.access_token
