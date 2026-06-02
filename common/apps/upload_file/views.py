from django.conf import settings
from rest_framework import generics, status
from rest_framework.response import Response

from common.apps.upload_file.serializers import PutPresignedURLSerializer
from common.apps.upload_file.service import get_presigned_url, put_presigned_url


class PutPresignedURL(generics.GenericAPIView):
    serializer_class = PutPresignedURLSerializer

    def put(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = put_presigned_url(
            settings.AWS_S3.get("AWS_STORAGE_BUCKET_NAME"),
            content_type=serializer.validated_data.get("content_type"),
        )
        if data is not None:
            return Response(data, status=status.HTTP_200_OK)

        return Response(
            {"error": "Get presigned url fail."}, status=status.HTTP_400_BAD_REQUEST
        )


class GetPresignedURL(generics.GenericAPIView):
    def get(self, request, *args, **kwargs):
        filename = self.kwargs.get("filename")
        link_file = f"uploads/{filename}"
        data = get_presigned_url(
            settings.AWS_S3.get("AWS_STORAGE_BUCKET_NAME"), link_file
        )
        if data is not None:
            return Response({"url_image": data}, status=status.HTTP_200_OK)

        return Response(
            {"error": "Get presigned url fail."}, status=status.HTTP_400_BAD_REQUEST
        )
