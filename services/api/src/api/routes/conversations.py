import datetime
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.auth import get_current_user
from api.db import get_db
from api.models.conversation import Contact, Conversation, Event, Message
from api.models.user import User
from api.schemas.conversation import (
    ConversationCreate,
    ConversationDetailResponse,
    ConversationExportResponse,
    ConversationMessageResponse,
    ConversationResponse,
    ConversationUpdate,
    MessageCreate,
)

router = APIRouter(prefix="/v1/conversations", tags=["conversations"])


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    payload: ConversationCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Conversation:
    # Validate contact belongs to user if provided
    if payload.contact_id:
        c_stmt = select(Contact).where(
            Contact.id == payload.contact_id,
            Contact.user_id == current_user.id,
        )
        c_res = await db.execute(c_stmt)
        if not c_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contact does not exist or does not belong to user",
            )

    # Validate event belongs to user if provided
    if payload.event_id:
        e_stmt = select(Event).where(
            Event.id == payload.event_id,
            Event.user_id == current_user.id,
        )
        e_res = await db.execute(e_stmt)
        if not e_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Event does not exist or does not belong to user",
            )

    conversation = Conversation(
        user_id=current_user.id,
        contact_id=payload.contact_id,
        event_id=payload.event_id,
        source=payload.source,
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return conversation


@router.get("", response_model=list[ConversationResponse])
async def list_conversations(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    event_id: Annotated[uuid.UUID | None, Query()] = None,
    contact_id: Annotated[uuid.UUID | None, Query()] = None,
    q: Annotated[str | None, Query(description="Search term for summary or message text")] = None,
) -> list[Conversation]:
    stmt = (
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .order_by(Conversation.started_at.desc())
    )

    if event_id:
        stmt = stmt.where(Conversation.event_id == event_id)
    if contact_id:
        stmt = stmt.where(Conversation.contact_id == contact_id)
    if q:
        search_filter = f"%{q}%"
        # Match either conversation summary or join messages
        subq = (
            select(Message.conversation_id)
            .where(Message.text.ilike(search_filter))
            .scalar_subquery()
        )
        stmt = stmt.where(
            or_(
                Conversation.summary.ilike(search_filter),
                Conversation.id.in_(subq),
            )
        )

    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Conversation:
    stmt = (
        select(Conversation)
        .options(
            selectinload(Conversation.contact),
            selectinload(Conversation.event),
            selectinload(Conversation.messages),
            selectinload(Conversation.suggestions),
        )
        .where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
    )
    result = await db.execute(stmt)
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    return conversation


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: uuid.UUID,
    payload: ConversationUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Conversation:
    stmt = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(conversation, field, value)

    await db.commit()
    await db.refresh(conversation)
    return conversation


@router.post(
    "/{conversation_id}/messages",
    response_model=ConversationMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_message(
    conversation_id: uuid.UUID,
    payload: MessageCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Message:
    stmt = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    if payload.seq is not None:
        seq = payload.seq
    else:
        # Compute next sequence number
        max_seq_stmt = select(func.coalesce(func.max(Message.seq), 0)).where(
            Message.conversation_id == conversation_id
        )
        max_res = await db.execute(max_seq_stmt)
        seq = int(max_res.scalar_one()) + 1

    message = Message(
        conversation_id=conversation_id,
        seq=seq,
        speaker=payload.speaker,
        text=payload.text,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    stmt = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    await db.delete(conversation)
    await db.commit()


@router.get("/{conversation_id}/export")
async def export_conversation(
    conversation_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    format: Annotated[str, Query(description="Export format: 'json' or 'text'")] = "json",
) -> Response:
    stmt = (
        select(Conversation)
        .options(
            selectinload(Conversation.contact),
            selectinload(Conversation.event),
            selectinload(Conversation.messages),
            selectinload(Conversation.suggestions),
        )
        .where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
    )
    result = await db.execute(stmt)
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    if format == "text":
        lines = [
            f"Conversation ID: {conversation.id}",
            f"Started: {conversation.started_at}",
            f"Ended: {conversation.ended_at or 'In Progress'}",
            f"Summary: {conversation.summary or 'None'}",
            f"Contact: {conversation.contact.name if conversation.contact else 'None'}",
            f"Event: {conversation.event.name if conversation.event else 'None'}",
            "",
            "--- TRANSCRIPT ---",
        ]
        for msg in conversation.messages:
            lines.append(f"[{msg.speaker.upper()} - #{msg.seq}] {msg.text}")
            matching_sugs = [s for s in conversation.suggestions if s.after_message_seq == msg.seq]
            for s in matching_sugs:
                lines.append(f"  [COACH SUGGESTION (rating: {s.rating or 'unrated'})] {s.text}")

        text_content = "\n".join(lines)
        return Response(
            content=text_content,
            media_type="text/plain",
            headers={
                "Content-Disposition": f'attachment; filename="conversation_{conversation_id}.txt"'
            },
        )

    # Default json export
    export_payload = ConversationExportResponse(
        conversation=ConversationResponse.model_validate(conversation),
        contact=conversation.contact,  # type: ignore[arg-type]
        event=conversation.event,  # type: ignore[arg-type]
        messages=[ConversationMessageResponse.model_validate(m) for m in conversation.messages],
        suggestions=conversation.suggestions,  # type: ignore[arg-type]
        exported_at=datetime.datetime.now(datetime.UTC),
    )
    return Response(
        content=export_payload.model_dump_json(indent=2),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="conversation_{conversation_id}.json"'
        },
    )
