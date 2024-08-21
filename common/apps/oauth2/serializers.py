from rest_framework import serializers


class OauthLoginSerializer(serializers.Serializer):
    authorization_code = serializers.CharField()
    code_verifier = serializers.CharField()
