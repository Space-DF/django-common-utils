from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.apps.upload_file.serializers import PresignedUploadSerializer
from common.apps.upload_file.service import get_file_url, put_presigned_url


def _resolve_org_slug(request):
    tenant = getattr(request, "tenant", None)
    if tenant and hasattr(tenant, "slug_name") and tenant.slug_name:
        return tenant.slug_name
    return request.headers.get("X-Organization", "")


def _resolve_user_id(request):
    return request.headers.get("X-User-ID", "")


class PutPresignedURL(APIView):
    def post(self, request):
        serializer = PresignedUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        org_slug = _resolve_org_slug(request)
        user_id = _resolve_user_id(request)

        if data["scope"] in ("org", "org_user") and not org_slug:
            return Response(
                {"error": "Organization could not be determined."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if data["scope"] in ("org_user", "root_user") and not user_id:
            return Response(
                {"error": "User ID is required for this scope."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = put_presigned_url(
            bucket_name=settings.AWS_S3.get("AWS_STORAGE_BUCKET_NAME"),
            file_name=data["file_name"],
            content_type=data["content_type"],
            visibility=data["visibility"],
            scope=data["scope"],
            org_slug=org_slug,
            user_id=user_id,
        )

        if result is not None:
            return Response(result, status=status.HTTP_200_OK)

        return Response(
            {"error": "Failed to generate presigned URL."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class GetPresignedURL(APIView):
    def get(self, request, *args, **kwargs):
        key = kwargs.get("key") or kwargs.get("filename")
        if not key:
            return Response(
                {"error": "File key is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        url = get_file_url(
            settings.AWS_S3.get("AWS_STORAGE_BUCKET_NAME"),
            key,
        )
        if url is not None:
            return Response({"url": url}, status=status.HTTP_200_OK)

        return Response(
            {"error": "Failed to generate URL."},
            status=status.HTTP_400_BAD_REQUEST,
        )
