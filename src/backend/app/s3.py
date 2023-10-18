"""Initialise the S3 buckets for FMTM to function."""

import sys
from io import BytesIO

from loguru import logger as log
from minio import Minio

from app.config import settings


def s3_client():
    """Return the initialised S3 client with credentials."""
    minio_url, is_secure = is_connection_secure(settings.S3_ENDPOINT)

    log.debug("Connecting to Minio S3 server")
    return Minio(
        minio_url,
        settings.S3_ACCESS_KEY,
        settings.S3_SECRET_KEY,
        secure=is_secure,
    )


def add_file_to_bucket(bucket_name: str, file_path: str, s3_path: str):
    """Upload a file from the filesystem to an S3 bucket.

    Args:
        bucket_name (str): The name of the S3 bucket.
        file_path (str): The path to the file on the local filesystem.
        s3_path (str): The path in the S3 bucket where the file will be stored.
    """
    client = s3_client()
    client.fput_object(bucket_name, file_path, s3_path)


def add_obj_to_bucket(bucket_name: str, file_obj: BytesIO, s3_path: str):
    """Upload a BytesIO object to an S3 bucket.

    Args:
        bucket_name (str): The name of the S3 bucket.
        file_obj (BytesIO): A BytesIO object containing the data to be uploaded.
        s3_path (str): The path in the S3 bucket where the data will be stored.
    """
    client = s3_client()
    result = client.put_object(bucket_name, file_obj, s3_path)
    log.debug(
        f"Created {result.object_name} object; etag: {result.etag}, "
        f"version-id: {result.version_id}"
    )


def get_file_from_bucket(bucket_name: str, s3_path: str, file_path: str):
    """Download a file from an S3 bucket and save it to the local filesystem.

    Args:
        bucket_name (str): The name of the S3 bucket.
        s3_path (str): The path to the file in the S3 bucket.
        file_path (str): The path on the local filesystem where the S3
            file will be saved.
    """
    client = s3_client()
    client.fget_object(bucket_name, s3_path, file_path)


def get_obj_from_bucket(bucket_name: str, s3_path: str) -> BytesIO:
    """Download an S3 object from a bucket and return it as a BytesIO object.

    Args:
        bucket_name (str): The name of the S3 bucket.
        s3_path (str): The path to the S3 object in the bucket.

    Returns:
        BytesIO: A BytesIO object containing the content of the downloaded S3 object.
    """
    client = s3_client()
    try:
        response = client.get_object(bucket_name, s3_path)
        return BytesIO(response.read())
    finally:
        response.close()
        response.release_conn()


def create_bucket_if_not_exists(client: Minio, bucket_name: str):
    """Checks if a bucket exits, else creates it."""
    if not client.bucket_exists(bucket_name):
        log.info(f"Creating S3 bucket: {bucket_name}")
        client.make_bucket(bucket_name)
    else:
        log.debug(f"S3 bucket already exists: {bucket_name}")


def is_connection_secure(minio_url: str):
    """Determine from URL string if is http or https."""
    if minio_url.startswith("http://"):
        secure = False
        stripped_url = minio_url[len("http://") :]
        log.warning("S3 URL is insecure (ignore if on devserver)")

    elif minio_url.startswith("https://"):
        secure = True
        stripped_url = minio_url[len("https://") :]

    else:
        err = (
            "The S3_ENDPOINT is set incorrectly. "
            "It must start with http:// or https://"
        )
        log.error(err)
        raise ValueError(err)

    return stripped_url, secure


def startup_init_buckets():
    """Wrapper to create defined buckets at startup."""
    # Logging
    log.remove()
    log.add(
        sys.stderr,
        level=settings.LOG_LEVEL,
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} "
            "| {name}:{function}:{line} | {message}"
        ),
        colorize=True,
        backtrace=True,  # More detailed tracebacks
        catch=True,  # Prevent app crashes
    )

    # Init S3 Buckets
    client = s3_client()
    create_bucket_if_not_exists(client, settings.S3_BUCKET_NAME_BASEMAPS)
    create_bucket_if_not_exists(client, settings.S3_BUCKET_NAME_OVERLAYS)


if __name__ == "__main__":
    startup_init_buckets()
