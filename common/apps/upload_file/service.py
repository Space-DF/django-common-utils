import logging
import uuid
from urllib.parse import unquote, urlsplit

import boto3
from botocore.exceptions import ClientError

client = boto3.client("s3")


def put_presigned_url(bucket_name, expiration=3600):
    """
    return presigned URL and file name
    """
    try:
        file_name = uuid.uuid4()
        presigned_url = client.generate_presigned_url(
            ClientMethod="put_object",
            Params={"Bucket": bucket_name, "Key": f"uploads/{file_name}"},
            ExpiresIn=expiration,
            HttpMethod="PUT",
        )
        return {"file_name": file_name, "presigned_url": presigned_url}
    except Exception as e:
        logging.error(f"Error: {e}")
        return None


def get_presigned_url(bucket_name, link_file, expiration=3600):
    """
    Return the URL from name file
    """
    try:
        url_image = client.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": bucket_name,
                "Key": link_file,
            },
            ExpiresIn=expiration,
        )
        return url_image
    except Exception as e:
        logging.error(f"Error generating presigned GET URL: {e}")
        return None


def normalize_s3_key(link_file: str, prefix: str = "uploads/") -> str:
    """
    Normalize S3 key from raw key or full URL.
    """
    key = link_file.strip()

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
        logging.error("Delete failed: missing bucket name or file key")
        return False

    key = normalize_s3_key(link_file)

    if not key:
        logging.error("Delete failed: empty S3 key after normalization")
        return False

    try:
        client.delete_object(Bucket=bucket_name, Key=key)
        logging.info(f"Deleted S3 object: bucket={bucket_name}, key={key}")
        return True

    except ClientError as e:
        logging.error(f"Delete failed: {str(e)}")
        return False
