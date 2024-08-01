import jwt
from rest_framework_simplejwt.backends import TokenBackend
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken


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


class CustomAccessToken(AccessToken):
    @property
    def token_backend(self):
        if self._token_backend is None:
            self._token_backend = token_backend
        return self._token_backend


class CustomRefreshToken(RefreshToken):
    access_token_class = CustomAccessToken

    @property
    def token_backend(self):
        if self._token_backend is None:
            self._token_backend = token_backend
        return self._token_backend
