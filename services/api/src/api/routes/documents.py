import re
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from api.db import get_db_session
from api.models.document import Document
from api.models.user import User
from api.schemas.document import (
    DocumentProcessResponse,
    DocumentResponse,
    DocumentUploadRequest,
    DocumentUploadResponse,
)
from api.services.queue import enqueue_document_job
from api.services.s3 import generate_presigned_upload_url

router = APIRouter(prefix="/v1/documents", tags=["documents"])


def sanitize_filename(filename: str) -> str:
    cleaned = re.sub(r"[^\w\.-]", "_", filename)
    return cleaned[:100]


@router.post(
    "/upload-url", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED
)
async def create_upload_url(
    payload: DocumentUploadRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> DocumentUploadResponse:
    """Generate a presigned S3 PUT URL for uploading a resume document."""
    doc_id = uuid.uuid4()
    clean_name = sanitize_filename(payload.filename)
    s3_key = f"users/{user.id}/documents/{doc_id}_{clean_name}"

    upload_url = generate_presigned_upload_url(s3_key, payload.mime)

    doc = Document(
        id=doc_id,
        user_id=user.id,
        s3_key=s3_key,
        filename=payload.filename,
        mime=payload.mime,
        status="uploaded",
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    return DocumentUploadResponse(
        document_id=doc.id,
        upload_url=upload_url,
        s3_key=doc.s3_key,
    )


@router.post(
    "/{document_id}/process",
    response_model=DocumentProcessResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def process_document(
    document_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> DocumentProcessResponse:
    """Trigger background text extraction and fact proposals for an uploaded document."""
    stmt = select(Document).where(
        Document.id == document_id,
        Document.user_id == user.id,
    )
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    doc.status = "parsing"
    await db.commit()

    # Enqueue SQS message for background worker
    enqueue_document_job(doc.id, user.id, doc.s3_key)

    return DocumentProcessResponse(
        document_id=doc.id,
        status="parsing",
        message="Document queued for parsing and fact extraction",
    )


@router.get("/{document_id}", response_model=DocumentResponse, status_code=status.HTTP_200_OK)
async def get_document(
    document_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> Document:
    """Retrieve document status and parsed text."""
    stmt = select(Document).where(
        Document.id == document_id,
        Document.user_id == user.id,
    )
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return doc


@router.get("", response_model=list[DocumentResponse], status_code=status.HTTP_200_OK)
async def list_documents(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[Document]:
    """List all documents uploaded by the authenticated user."""
    stmt = select(Document).where(Document.user_id == user.id).order_by(Document.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())
