import logging
import os
import uuid
from urllib.parse import unquote, urlsplit

import boto3
from django.conf import settings
from django.utils.text import get_valid_filename

logger = logging.getLogger(__name__)

_s3_client = None


def _get_s3_client():
    global _s3_client
    if _s3_client is None:
        aws_config = getattr(settings, "AWS_S3", {})
        _s3_client = boto3.client(
            "s3",
            aws_access_key_id=aws_config.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=aws_config.get("AWS_SECRET_ACCESS_KEY"),
            region_name=aws_config.get("AWS_REGION"),
        )
    return _s3_client


def put_presigned_url(
    bucket_name,
    file_name,
    content_type,
    org_slug,
    visibility="private",
    expiration=3600,
):
    """
    Generate a presigned URL for PUT upload to S3.

    Args:
        bucket_name: S3 bucket name.
        file_name: Original file name (e.g. "avatar.png").
        content_type: MIME type (e.g. "image/png").
        orgSlug: Organization slug for namespacing files.
        visibility: "public" or "private".
        expiration: URL expiration in seconds.

    Returns:
        dict with "presigned_url" and "file_path", or None on failure.
    """
    client = _get_s3_client()

    clean_name = get_valid_filename(os.path.basename(file_name))
    unique_file_name = f"{uuid.uuid4()}_{clean_name}"
    key = f"{visibility}/organizations/{org_slug}/{unique_file_name}"

    params = {
        "Bucket": bucket_name,
        "Key": key,
        "ContentType": content_type,
    }

    # Note: Setting ACL to "public-read" is not recommended for security reasons.
    # if visibility == "public":
    #     params["ACL"] = "public-read"

    try:
        presigned_url = client.generate_presigned_url(
            ClientMethod="put_object",
            Params=params,
            ExpiresIn=expiration,
            HttpMethod="PUT",
        )
        return {"presigned_url": presigned_url, "file_path": key}
    except Exception as e:
        logger.error(f"Failed to generate PUT presigned URL: {e}")
        return None


def get_public_url(bucket_name, file_path):
    """
    Build a permanent public URL for a public S3 object.

    Args:
        bucket_name: S3 bucket name.
        file_path: Full S3 key starting with 'public/'.

    Returns:
        Permanent public URL string.
    """
    aws_config = getattr(settings, "AWS_S3", {})
    region = aws_config.get("AWS_REGION", "us-east-1")
    key = normalize_s3_key(file_path)
    return f"https://{bucket_name}.s3.{region}.amazonaws.com/{key}"


def get_presigned_url(bucket_name, file_path, expiration=3600):
    """
    Generate a presigned GET URL for an S3 object.

    Args:
        bucket_name: S3 bucket name.
        file_path: Full S3 key (e.g. "public/uuid_avatar.png").
        expiration: URL expiration in seconds.

    Returns:
        Presigned URL string, or None on failure.
    """
    client = _get_s3_client()

    key = normalize_s3_key(file_path)

    try:
        return client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": bucket_name, "Key": key},
            ExpiresIn=expiration,
            HttpMethod="GET",
        )
    except Exception as e:
        logger.error(f"Failed to generate GET presigned URL: {e}")
        return None


def normalize_s3_key(link_file: str, prefix: str = "") -> str:
    """
    Normalize an S3 key from a raw key or full URL.
    """
    key = (link_file or "").strip()

    parsed = urlsplit(key)
    if parsed.scheme or parsed.netloc:
        key = parsed.path

    key = unquote(key).lstrip("/")

    if key and prefix and not key.startswith(prefix):
        key = f"{prefix}{key}"

    return key


def delete_file(bucket_name: str, link_file: str) -> bool:
    """
    Delete file from S3 bucket.
    """
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
