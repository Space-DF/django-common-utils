from django.urls import path

from common.apps.upload_file.views import GetPresignedURL, PutPresignedURL

urlpatterns = [
    path("presigned-url", PutPresignedURL.as_view(), name="presigned_url"),
    path(
        "presigned-url/<str:filename>",
        GetPresignedURL.as_view(),
        name="get_presigned_url",
    ),
]
