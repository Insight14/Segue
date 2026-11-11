import json
import logging
import uuid
from typing import Any

import boto3
from botocore.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from worker.config import get_worker_settings
from worker.extractor import extract_candidate_facts
from worker.parser import extract_text_from_pdf

logger = logging.getLogger("convo-glasses-processor")


def get_s3_client() -> Any:
    settings = get_worker_settings()
    endpoint = settings.S3_ENDPOINT_URL if settings.S3_ENDPOINT_URL else None
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=settings.S3_ACCESS_KEY_ID,
        aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        region_name=settings.S3_REGION,
        config=Config(signature_version="s3v4"),
    )


async def process_document_job(
    job_payload: dict[str, Any],
    engine: AsyncEngine | None = None,
    s3_client: Any | None = None,
) -> bool:
    """Process a single document job from SQS:

    1. Download PDF from S3.
    2. Extract plain text safely.
    3. Extract proposed facts (ALWAYS confirmed=False).
    4. Save to database.
    """
    settings = get_worker_settings()
    doc_id_str = job_payload.get("document_id")
    user_id_str = job_payload.get("user_id")
    s3_key = job_payload.get("s3_key")

    if not doc_id_str or not user_id_str or not s3_key:
        logger.error("Invalid job payload: %s", job_payload)
        return False

    doc_id = uuid.UUID(doc_id_str)
    user_id = uuid.UUID(user_id_str)

    if engine is None:
        engine = create_async_engine(settings.DATABASE_URL)
    if s3_client is None:
        s3_client = get_s3_client()

    logger.info("Processing document %s for user %s (s3_key=%s)", doc_id, user_id, s3_key)

    try:
        # 1. Download file from S3
        resp = s3_client.get_object(Bucket=settings.S3_BUCKET_NAME, Key=s3_key)
        pdf_bytes = resp["Body"].read()

        # 2. Extract text from PDF
        parsed_text = extract_text_from_pdf(pdf_bytes)

        # 3. Extract candidate facts
        proposed_facts = extract_candidate_facts(parsed_text)

        # 4. Save to database within transaction
        async with engine.begin() as conn:
            # Update document to parsed
            update_sql = """
                UPDATE documents
                SET status = 'parsed', parsed_text = :text, updated_at = CURRENT_TIMESTAMP
                WHERE id = :doc_id
            """
            await conn.execute(text(update_sql), {"text": parsed_text, "doc_id": str(doc_id)})

            # Insert proposed facts with confirmed=False
            insert_fact_sql = """
                INSERT INTO profile_facts (
                    id, user_id, kind, title, body, tags, source, confirmed, created_at, updated_at
                ) VALUES (
                    :id, :user_id, :kind, :title, :body, :tags, :source, :confirmed,
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
            """
            for fact in proposed_facts:
                fact_id = uuid.uuid4()
                await conn.execute(
                    text(insert_fact_sql),
                    {
                        "id": str(fact_id),
                        "user_id": str(user_id),
                        "kind": fact["kind"],
                        "title": fact["title"],
                        "body": fact["body"],
                        "tags": json.dumps(fact["tags"]),
                        "source": "resume",
                        "confirmed": False,  # ACCEPTANCE CRITERIA: NEVER AUTO-CONFIRMED
                    },
                )

        logger.info(
            "Successfully processed document %s: extracted %d proposed facts",
            doc_id,
            len(proposed_facts),
        )
        return True

    except Exception as err:
        logger.error("Error processing document %s: %s", doc_id, err, exc_info=True)
        try:
            fail_sql = """
                UPDATE documents
                SET status = 'failed', error_message = :err, updated_at = CURRENT_TIMESTAMP
                WHERE id = :doc_id
            """
            async with engine.begin() as conn:
                await conn.execute(
                    text(fail_sql),
                    {"err": str(err)[:500], "doc_id": str(doc_id)},
                )
        except Exception as db_err:
            logger.error("Failed to update document failure status: %s", db_err)
        return False
