from rest_framework import serializers


class PutPresignedURLSerializer(serializers.Serializer):
    content_type = serializers.CharField()
