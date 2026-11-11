import io
import uuid
from unittest.mock import MagicMock

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool
from test_parser import SAMPLE_PDF_BYTES

from worker.processor import process_document_job


@pytest.mark.asyncio
async def test_process_document_job_end_to_end() -> None:
    # 1. Setup in-memory SQLite database matching production schema
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.execute(
            text(
                """
                CREATE TABLE documents (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    s3_key TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    mime TEXT NOT NULL,
                    status TEXT NOT NULL,
                    parsed_text TEXT,
                    error_message TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                );
                """
            )
        )
        await conn.execute(
            text(
                """
                CREATE TABLE profile_facts (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    title TEXT NOT NULL,
                    body TEXT NOT NULL,
                    tags JSON NOT NULL,
                    source TEXT NOT NULL,
                    confirmed BOOLEAN NOT NULL,
                    embedding TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                );
                """
            )
        )

        doc_id = uuid.uuid4()
        user_id = uuid.uuid4()
        s3_key = f"users/{user_id}/documents/{doc_id}_resume.pdf"

        await conn.execute(
            text(
                """
                INSERT INTO documents (id, user_id, s3_key, filename, mime, status)
                VALUES (:id, :user_id, :s3_key, 'resume.pdf', 'application/pdf', 'parsing')
                """
            ),
            {"id": str(doc_id), "user_id": str(user_id), "s3_key": s3_key},
        )

    # 2. Mock S3 client returning our sample PDF bytes
    mock_s3 = MagicMock()
    mock_s3.get_object.return_value = {"Body": io.BytesIO(SAMPLE_PDF_BYTES)}

    job_payload = {
        "job_type": "parse_resume",
        "document_id": str(doc_id),
        "user_id": str(user_id),
        "s3_key": s3_key,
    }

    # 3. Execute worker processing
    success = await process_document_job(job_payload, engine=engine, s3_client=mock_s3)
    assert success is True

    # 4. Verify Document status in database
    async with engine.connect() as conn:
        doc_res = await conn.execute(
            text("SELECT status, parsed_text FROM documents WHERE id = :id"),
            {"id": str(doc_id)},
        )
        doc_row = doc_res.mappings().one()
        assert doc_row["status"] == "parsed"
        assert "Jane Doe" in doc_row["parsed_text"]

        # 5. VERIFY ACCEPTANCE CRITERIA:
        # Sample PDF yields proposed facts; nothing is saved as confirmed without user action!
        fact_query = """
            SELECT id, kind, title, source, confirmed
            FROM profile_facts
            WHERE user_id = :user_id
        """
        facts_res = await conn.execute(text(fact_query), {"user_id": str(user_id)})
        facts = list(facts_res.mappings().all())
        assert len(facts) > 0, "Sample PDF must yield proposed facts"

        for fact in facts:
            assert (
                fact["confirmed"] is False or fact["confirmed"] == 0
            ), "Proposed facts MUST NOT be saved as confirmed without user action!"
            assert fact["source"] == "resume"

    await engine.dispose()


@pytest.mark.asyncio
async def test_process_document_job_invalid_pdf_failure() -> None:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.execute(
            text(
                """
                CREATE TABLE documents (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    s3_key TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    mime TEXT NOT NULL,
                    status TEXT NOT NULL,
                    parsed_text TEXT,
                    error_message TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                );
                """
            )
        )
        doc_id = uuid.uuid4()
        user_id = uuid.uuid4()
        s3_key = "invalid.pdf"
        insert_doc_sql = """
            INSERT INTO documents (id, user_id, s3_key, filename, mime, status)
            VALUES (:id, :user_id, :s3_key, 'inv.pdf', 'application/pdf', 'parsing')
        """
        await conn.execute(
            text(insert_doc_sql),
            {"id": str(doc_id), "user_id": str(user_id), "s3_key": s3_key},
        )

    mock_s3 = MagicMock()
    mock_s3.get_object.return_value = {"Body": io.BytesIO(b"garbage bytes not pdf")}

    job_payload = {
        "job_type": "parse_resume",
        "document_id": str(doc_id),
        "user_id": str(user_id),
        "s3_key": s3_key,
    }

    success = await process_document_job(job_payload, engine=engine, s3_client=mock_s3)
    assert success is False

    async with engine.connect() as conn:
        doc_res = await conn.execute(
            text("SELECT status, error_message FROM documents WHERE id = :id"),
            {"id": str(doc_id)},
        )
        doc_row = doc_res.mappings().one()
        assert doc_row["status"] == "failed"
        assert doc_row["error_message"] is not None

    await engine.dispose()
