import jwt
from django.db import connection
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.backends import TokenBackend
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from common.utils.subdomain import extract_subdomain


class CustomTokenBackend(TokenBackend):
    def encode(self, payload):
        """
        Returns an encoded token for the given payload dictionary.
        """
        jwt_payload = payload.copy()
        if self.audience is not None:
            jwt_payload["aud"] = self.audience
        if self.issuer is not None:
            jwt_payload["iss"] = self.issuer
        token = jwt.encode(
            jwt_payload,
            self.signing_key,
            algorithm=self.algorithm,
            json_encoder=self.json_encoder,
            headers={"kid": "default"},
        )

        return token

    def set_iss(self, issuer: str):
        self.issuer = issuer


token_backend = CustomTokenBackend(
    api_settings.ALGORITHM,
    api_settings.SIGNING_KEY,
    api_settings.VERIFYING_KEY,
    api_settings.AUDIENCE,
    api_settings.ISSUER,
    api_settings.JWK_URL,
    api_settings.LEEWAY,
    api_settings.JSON_ENCODER,
)


class TokenVerifier:
    def verify(self) -> None:
        self.check_iss()
        return super().verify()

    def check_iss(self):
        issuer = self.payload.get("iss", None)
        if not issuer:
            raise AuthenticationFailed("Token is not valid")
        subdomain = extract_subdomain(issuer)
        if not subdomain or subdomain != connection.tenant.slug_name:
            raise AuthenticationFailed("Token is not valid")


class CustomAccessToken(TokenVerifier, AccessToken):
    @property
    def token_backend(self):
        if self._token_backend is None:
            self._token_backend = token_backend
        return self._token_backend


class CustomRefreshToken(TokenVerifier, RefreshToken):
    access_token_class = CustomAccessToken

    @property
    def token_backend(self):
        if self._token_backend is None:
            self._token_backend = token_backend
        return self._token_backend

    def set_iss(self, claim: str = "iss", issuer=None) -> None:
        self.token_backend.set_iss(issuer=issuer)
        self.payload[claim] = issuer
