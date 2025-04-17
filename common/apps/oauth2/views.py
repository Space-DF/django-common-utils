import logging
from operator import itemgetter

import requests
from django.conf import settings
from django.shortcuts import redirect
from rest_framework import generics, status
from rest_framework.exceptions import ParseError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from common.apps.oauth2.serializers import CodeLoginSerializer, OauthLoginSerializer
from common.utils.encoder import decode_from_base64
from common.utils.oauth2 import get_access_token, handle_access_token


class GoogleLoginView(generics.CreateAPIView):
    serializer_class = OauthLoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            authorization_code, code_verifier = itemgetter(
                "authorization_code", "code_verifier"
            )(serializer.validated_data)
            try:
                access_token = get_access_token(
                    authorization_code=authorization_code,
                    code_verifier=code_verifier,
                    provider="GOOGLE",
                )
                return handle_access_token(access_token=access_token, provider="GOOGLE")
            except Exception as e:
                logging.exception(e)
                raise ParseError(detail="Bad request")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GoogleLoginCallbackView(generics.RetrieveAPIView):

    def get(self, request):
        code = request.GET.get("code")
        state = request.GET.get("state")

        if not code or not state:
            return Response({"error": "Missing code or state"}, status=400)

        try:
            state_data = decode_from_base64(state)
            callback_url = state_data["callback_url"]
        except Exception as e:
            return Response({"error": str(e)}, status=400)
        fe_redirect_url = f"{callback_url}?code={code}&state={state}"
        return redirect(fe_redirect_url)


class GoogleLoginTokenView(generics.CreateAPIView):
    serializer_class = CodeLoginSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        authorization_code = serializer.validated_data["authorization_code"]
        provider_settings = settings.SOCIALACCOUNT_PROVIDERS.get("google", {}).get(
            "APP"
        )

        token_url = settings.OAUTH_CLIENTS["GOOGLE"]["TOKEN_URL"]
        data = {
            "code": authorization_code,
            "client_id": provider_settings.get("client_id"),
            "client_secret": provider_settings.get("secret"),
            "redirect_uri": settings.OAUTH_CLIENTS["GOOGLE"]["CALLBACK_URL"],
            "grant_type": "authorization_code",
        }

        token_resp = requests.post(token_url, data=data, timeout=5)
        if token_resp.status_code != 200:
            return Response(
                {"error": "Failed to get token", "detail": token_resp.json()},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token_data = token_resp.json()
        access_token = token_data.get("access_token")

        return handle_access_token(access_token=access_token, provider="GOOGLE")
