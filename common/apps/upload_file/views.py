from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from common.apps.upload_file.serializers import PresignedUploadSerializer
from common.apps.upload_file.service import (
    get_presigned_url,
    get_public_url,
    put_presigned_url,
)


def _resolve_org_slug(request):
    tenant = getattr(request, "tenant", None)
    if tenant is not None:
        return tenant.slug_name

    org_slug = request.headers.get("X-Organization", "").strip()
    if org_slug:
        return org_slug

    return "shared"


class PutPresignedURL(APIView):
    """
    Generate a presigned URL for PUT upload to S3.

    Request body:
        file_name: Name of the file to be uploaded.
        content_type: MIME type of the file (e.g. image/png, image/jpeg).
        visibility: Storage visibility, either "public" or "private".

    Returns:
        presigned_url: The presigned PUT URL.
        file_path: The final S3 object key to store in the database.
    """

    @swagger_auto_schema(
        request_body=PresignedUploadSerializer,
        responses={
            200: "Presigned URL generated successfully",
            500: "Internal server error",
        },
    )
    def post(self, request):
        serializer = PresignedUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        bucket_name = settings.AWS_S3.get("AWS_STORAGE_BUCKET_NAME")
        org_slug = _resolve_org_slug(request)
        data = put_presigned_url(
            bucket_name=bucket_name,
            file_name=serializer.validated_data["file_name"],
            content_type=serializer.validated_data["content_type"],
            org_slug=org_slug,
            visibility=serializer.validated_data["visibility"],
        )

        if data is not None:
            return Response(data, status=status.HTTP_200_OK)

        return Response(
            {"error": "Failed to generate presigned URL."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class GetPresignedURL(APIView):
    """
    Generate a presigned GET URL for an S3 object.

    Path param:
        file_path: The full S3 key (e.g. public/organizations/org/uuid_avatar.png).
    """

    permission_classes = [AllowAny]

    def get(self, request, file_path):
        if not (file_path.startswith("public/") or file_path.startswith("private/")):
            return Response(
                {"error": "Access denied: Invalid file path prefix."},
                status=status.HTTP_403_FORBIDDEN,
            )

        aws_s3_config = getattr(settings, "AWS_S3", {})
        bucket_name = aws_s3_config.get("AWS_STORAGE_BUCKET_NAME")

        if file_path.startswith("public/"):
            url = get_public_url(bucket_name, file_path)
            return Response({"url": url}, status=status.HTTP_200_OK)

        if not request.user.is_authenticated:
            return Response(
                {"error": "Authentication required for private files."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        url = get_presigned_url(bucket_name, file_path)

        if url is not None:
            return Response({"url": url}, status=status.HTTP_200_OK)

        return Response(
            {"error": "Failed to generate presigned URL."},
            status=status.HTTP_400_BAD_REQUEST,
        )
