from typing import Any

import boto3
from botocore.config import Config
from fastapi import HTTPException, status

from api.config import get_settings

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}


def get_s3_client() -> Any:
    settings = get_settings()
    endpoint = settings.S3_ENDPOINT_URL if settings.S3_ENDPOINT_URL else None
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=settings.S3_ACCESS_KEY_ID,
        aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        region_name=settings.S3_REGION,
        config=Config(signature_version="s3v4"),
    )


def generate_presigned_upload_url(s3_key: str, mime: str, expires_in: int = 3600) -> str:
    if mime not in ALLOWED_MIME_TYPES:
        allowed = ", ".join(sorted(ALLOWED_MIME_TYPES))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{mime}'. Allowed types: {allowed}",
        )

    settings = get_settings()
    s3 = get_s3_client()
    url: str = s3.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": settings.S3_BUCKET_NAME,
            "Key": s3_key,
            "ContentType": mime,
        },
        ExpiresIn=expires_in,
    )
    return url
