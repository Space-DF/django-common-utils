from authlib.jose import JsonWebKey
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class JWKView(APIView):
    def get(self, _):
        public_key = JsonWebKey.import_key(
            settings.JWT_PUBLIC_KEY, {"kty": "RSA", "kid": "1"}
        )

        return Response({"keys": [public_key]}, status=status.HTTP_200_OK)
