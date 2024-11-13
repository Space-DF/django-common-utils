import urllib.parse
from operator import itemgetter
from typing import Literal

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.response import Response

from common.apps.refresh_tokens.services import create_jwt_tokens

User = get_user_model()


def decode_uri_component(code: str):
    return urllib.parse.unquote(code)


def get_access_token(
    authorization_code: str, code_verifier: str, provider: Literal["GOOGLE"]
) -> str:
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    token_url = settings.OAUTH_CLIENTS[provider]["TOKEN_URL"]

    if provider == "GOOGLE":
        authorization_code = decode_uri_component(authorization_code)
    payload = {
        "grant_type": "authorization_code",
        "code": authorization_code,
        "redirect_uri": settings.OAUTH_CLIENTS[provider]["CALLBACK_URL"],
        "code_verifier": code_verifier,
        "client_id": settings.OAUTH_CLIENTS[provider]["CLIENT_ID"],
        "client_secret": settings.OAUTH_CLIENTS[provider]["CLIENT_SECRET"],
    }
    response = requests.post(
        url=token_url, data=urllib.parse.urlencode(payload), headers=headers, timeout=10
    )
    response.raise_for_status()
    return response.json()["access_token"]


def handle_access_token(access_token, provider: Literal["GOOGLE"]):
    info_url = settings.OAUTH_CLIENTS[provider]["INFO_URL"]

    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.post(url=info_url, headers=headers, timeout=10)
    response.raise_for_status()
    user_info_dict = response.json()
    given_name, family_name, email = itemgetter("given_name", "family_name", "email")(
        user_info_dict
    )
    root_user, is_created = User.objects.get_or_create(
        email=email,
    )
    if is_created:
        root_user.first_name = given_name
        root_user.last_name = family_name
        root_user.save()

    if provider.lower() not in root_user.providers:
        root_user.providers.append(provider.lower())
        root_user.save()

    refresh, access = create_jwt_tokens(root_user)
    return Response(
        status=status.HTTP_200_OK, data={"refresh": str(refresh), "access": str(access)}
    )
