import logging
import uuid
from urllib.parse import unquote, urlsplit

import boto3
from botocore.client import Config
from django.conf import settings

_s3_client = None

logger = logging.getLogger(__name__)


def _get_s3_client():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
            ),
            region_name=settings.AWS_S3.get("AWS_REGION", "ap-southeast-1"),
        )
    return _s3_client


def _build_s3_key(visibility, scope, file_name, org_slug=None, user_id=None):
    unique_name = f"{uuid.uuid4().hex}_{file_name}"

    if scope == "root_user":
        return f"{visibility}/root_users/{user_id}/{unique_name}"

    if scope == "org_user":
        return f"{visibility}/organizations/{org_slug}/users/{user_id}/{unique_name}"

    return f"{visibility}/organizations/{org_slug}/{unique_name}"


def put_presigned_url(
    bucket_name,
    file_name,
    content_type,
    visibility,
    scope,
    org_slug=None,
    user_id=None,
    expiration=3600,
):
    try:
        key = _build_s3_key(visibility, scope, file_name, org_slug, user_id)
        client = _get_s3_client()

        params = {
            "Bucket": bucket_name,
            "Key": key,
            "ContentType": content_type,
        }

        presigned_url = client.generate_presigned_url(
            ClientMethod="put_object",
            Params=params,
            ExpiresIn=expiration,
            HttpMethod="PUT",
        )
        return {"key": key, "presigned_url": presigned_url}
    except Exception as e:
        logger.error(f"Error generating presigned PUT URL: {e}")
        return None


def get_file_url(bucket_name, key, expiration=3600):
    if not key:
        return None

    key = normalize_s3_key(key)

    if not key:
        return None

    if key.startswith("public/"):
        region = (
            settings.AWS_REGION if hasattr(settings, "AWS_REGION") else "ap-southeast-1"
        )
        return f"https://s3.{region}.amazonaws.com/{bucket_name}/{key}"

    return get_presigned_url(bucket_name, key, expiration)


def get_presigned_url(bucket_name, link_file, expiration=3600):
    try:
        client = _get_s3_client()
        url_image = client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": bucket_name, "Key": link_file},
            ExpiresIn=expiration,
            HttpMethod="GET",
        )
        return url_image
    except Exception as e:
        logger.error(f"Failed to generate GET presigned URL: {e}")
        return None


def normalize_s3_key(link_file: str, prefix: str = "") -> str:
    key = link_file.strip()

    parsed = urlsplit(key)
    if parsed.scheme or parsed.netloc:
        key = parsed.path

    key = unquote(key).lstrip("/")

    if key and prefix and not key.startswith(prefix):
        key = f"{prefix}{key}"

    return key


def delete_file(bucket_name: str, link_file: str) -> bool:
    if not bucket_name or not link_file:
        logger.error("Delete failed: missing bucket name or file key")
        return False

    client = _get_s3_client()
    key = normalize_s3_key(link_file)

    if not key:
        logger.error("Delete failed: empty S3 key after normalization")
        return False

    try:
        client.delete_object(Bucket=bucket_name, Key=key)
        logger.info(f"Deleted S3 object: bucket={bucket_name}, key={key}")
        return True
    except Exception as e:
        logger.error(f"Delete failed: {e}")
        return False
