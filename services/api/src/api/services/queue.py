import json
import logging
import uuid
from typing import Any

import boto3
from botocore.config import Config

from api.config import get_settings

logger = logging.getLogger("convo-glasses-queue")


def get_sqs_client() -> Any:
    settings = get_settings()
    endpoint = settings.SQS_ENDPOINT_URL if settings.SQS_ENDPOINT_URL else None
    return boto3.client(
        "sqs",
        endpoint_url=endpoint,
        aws_access_key_id=settings.S3_ACCESS_KEY_ID,
        aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        region_name=settings.SQS_REGION,
        config=Config(signature_version="s3v4"),
    )


def enqueue_document_job(document_id: uuid.UUID, user_id: uuid.UUID, s3_key: str) -> None:
    settings = get_settings()
    sqs = get_sqs_client()
    payload = {
        "job_type": "parse_resume",
        "document_id": str(document_id),
        "user_id": str(user_id),
        "s3_key": s3_key,
    }
    try:
        sqs.send_message(
            QueueUrl=settings.SQS_QUEUE_URL,
            MessageBody=json.dumps(payload),
        )
        logger.info("Enqueued resume parsing job for document %s", document_id)
    except Exception as err:
        logger.error("Failed to enqueue document job: %s", err)
