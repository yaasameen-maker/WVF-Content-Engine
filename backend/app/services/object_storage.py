"""
Cloudflare R2 object storage — direct-to-storage presigned uploads for
the photo library (app/routers/media.py) and AI-generated images
(app/routers/image_generation.py). Neither feature is built by routing
file bytes through this backend: the browser uploads straight to R2
using a short-lived presigned PUT URL this module generates, and the
backend only ever stores metadata (object key, public URL, size,
content type) in Postgres.

R2 is S3-compatible, so this uses boto3's S3 client pointed at R2's
account-scoped endpoint rather than a Cloudflare-specific SDK. The
bucket is public-read (photos and generated images aren't sensitive —
unlike social_connections' OAuth tokens, see token_encryption.py), so
reads are just the stored public_url string; only uploads need signing.

Requires R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY,
R2_BUCKET_NAME, R2_PUBLIC_BASE_URL — all generated from the Cloudflare
dashboard (R2 > Manage R2 API Tokens for the access key pair; the
bucket's public URL, either its r2.dev subdomain or a custom domain,
for R2_PUBLIC_BASE_URL). See backend/.env.example for details.
"""

import os
import uuid

import boto3
from botocore.client import Config

PRESIGNED_UPLOAD_EXPIRY_SECONDS = 300  # 5 minutes — long enough for a real upload, short enough that a leaked URL is low-risk


def _get_r2_client():
    account_id = os.getenv("R2_ACCOUNT_ID")
    access_key_id = os.getenv("R2_ACCESS_KEY_ID")
    secret_access_key = os.getenv("R2_SECRET_ACCESS_KEY")
    if not account_id or not access_key_id or not secret_access_key:
        raise ValueError(
            "R2_ACCOUNT_ID / R2_ACCESS_KEY_ID / R2_SECRET_ACCESS_KEY environment variables not set "
            "— required for photo/image uploads. Generate an API token under the Cloudflare "
            "dashboard's R2 > Manage R2 API Tokens."
        )
    return boto3.client(
        "s3",
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        # R2 only supports SigV4, and region is a required-but-ignored
        # field for R2's S3-compatible API — "auto" is R2's documented value.
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


def _get_bucket_name() -> str:
    bucket = os.getenv("R2_BUCKET_NAME")
    if not bucket:
        raise ValueError("R2_BUCKET_NAME environment variable not set — required for photo/image uploads.")
    return bucket


def build_object_key(prefix: str, filename: str) -> str:
    """Builds a collision-proof storage key, e.g. 'photos/3f2a.../headshot.jpg'.
    UUID-prefixed rather than trusting the original filename to be unique —
    two staff uploading files both named "IMG_001.jpg" shouldn't collide."""
    safe_filename = filename.replace("/", "_").replace("\\", "_")
    return f"{prefix}/{uuid.uuid4()}/{safe_filename}"


def generate_presigned_upload_url(object_key: str, content_type: str) -> str:
    """Returns a URL the browser can PUT the file bytes to directly —
    this backend never receives the file itself. Expires after
    PRESIGNED_UPLOAD_EXPIRY_SECONDS."""
    client = _get_r2_client()
    return client.generate_presigned_url(
        "put_object",
        Params={"Bucket": _get_bucket_name(), "Key": object_key, "ContentType": content_type},
        ExpiresIn=PRESIGNED_UPLOAD_EXPIRY_SECONDS,
    )


def build_public_url(object_key: str) -> str:
    """The stable, permanent read URL for an object once uploaded —
    no signing needed since the bucket is public-read."""
    base = os.getenv("R2_PUBLIC_BASE_URL")
    if not base:
        raise ValueError("R2_PUBLIC_BASE_URL environment variable not set — required for photo/image uploads.")
    return f"{base.rstrip('/')}/{object_key}"


def delete_object(object_key: str) -> None:
    """Best-effort delete — callers (e.g. DELETE /api/media/photos/{id})
    should remove the DB row regardless of whether this succeeds; the DB
    row, not the R2 object, is the source of truth for what the library
    considers to exist."""
    client = _get_r2_client()
    client.delete_object(Bucket=_get_bucket_name(), Key=object_key)
