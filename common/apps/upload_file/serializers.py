from rest_framework import serializers


class PresignedUploadSerializer(serializers.Serializer):
    file_name = serializers.CharField(
        required=True,
        max_length=255,
        help_text="Name of the file to be uploaded (e.g. avatar.png)",
    )
    content_type = serializers.CharField(
        required=True,
        max_length=127,
        help_text="MIME type of the file (e.g. image/png, image/jpeg)",
    )
    visibility = serializers.ChoiceField(
        choices=["public", "private"],
        default="private",
        help_text="Storage visibility: public or private",
    )
    scope = serializers.ChoiceField(
        choices=["org", "org_user", "root_user"],
        default="org",
        help_text="Upload scope: org, org_user, or root_user",
    )
