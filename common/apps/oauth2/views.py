import logging
from operator import itemgetter

from rest_framework import generics, status
from rest_framework.exceptions import ParseError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from common.apps.oauth2.serializers import OauthLoginSerializer
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
