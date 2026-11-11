import json
import uuid
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.agent.discover import determine_next_discover_question, propose_fact_from_user_response
from api.agent.provider import get_llm_provider
from api.auth import get_current_user
from api.db import get_db_session
from api.models.agent import AgentMessage, AgentThread
from api.models.user import User
from api.schemas.agent import (
    SendMessageRequest,
    ThreadCreateRequest,
    ThreadResponse,
)

router = APIRouter(prefix="/v1/agent/threads", tags=["guide-agent"])


@router.post("", response_model=ThreadResponse, status_code=status.HTTP_201_CREATED)
async def create_thread(
    payload: ThreadCreateRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> AgentThread:
    """Create a new guide agent conversation thread in Discover or Prep mode."""
    thread = AgentThread(
        user_id=user.id,
        mode=payload.mode.value,
        title=payload.title,
    )
    db.add(thread)
    await db.commit()
    await db.refresh(thread)

    # Initial greeting message from agent
    greeting_prep = "Ready to prepare talking points. Who are you speaking with or which event?"
    initial_content = (
        determine_next_discover_question(0) if payload.mode.value == "discover" else greeting_prep
    )
    msg = AgentMessage(
        thread_id=thread.id,
        role="assistant",
        content=initial_content,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(thread, attribute_names=["messages"])
    return thread


@router.get("", response_model=list[ThreadResponse], status_code=status.HTTP_200_OK)
async def list_threads(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[AgentThread]:
    """List all agent conversation threads belonging to the authenticated user."""
    stmt = (
        select(AgentThread)
        .where(AgentThread.user_id == user.id)
        .options(selectinload(AgentThread.messages))
        .order_by(AgentThread.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/{thread_id}", response_model=ThreadResponse, status_code=status.HTTP_200_OK)
async def get_thread(
    thread_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> AgentThread:
    """Get a specific thread and its full message history."""
    stmt = (
        select(AgentThread)
        .where(AgentThread.id == thread_id, AgentThread.user_id == user.id)
        .options(selectinload(AgentThread.messages))
    )
    result = await db.execute(stmt)
    thread = result.scalar_one_or_none()
    if not thread:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")
    return thread


@router.post("/{thread_id}/messages")
async def send_message_stream(
    thread_id: uuid.UUID,
    payload: SendMessageRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> StreamingResponse:
    """Send a user message to the thread and stream the assistant's reply over SSE."""
    stmt = (
        select(AgentThread)
        .where(AgentThread.id == thread_id, AgentThread.user_id == user.id)
        .options(selectinload(AgentThread.messages))
    )
    result = await db.execute(stmt)
    thread = result.scalar_one_or_none()
    if not thread:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")

    # 1. Save user message
    user_msg = AgentMessage(
        thread_id=thread.id,
        role="user",
        content=payload.content,
    )
    db.add(user_msg)
    await db.commit()

    # 2. In Discover mode, check if we can propose a fact
    proposed_fact = None
    if thread.mode == "discover":
        proposed_fact = propose_fact_from_user_response(payload.content)

    provider = get_llm_provider()
    system_prompt = (
        f"You are the Convo Glasses AI guide in {thread.mode} mode. "
        "Be encouraging, concise, and ask ONE focused question at a time."
    )

    async def event_generator() -> AsyncGenerator[str, None]:
        full_reply_chunks: list[str] = []

        async for chunk in provider.stream(payload.content, system_prompt):
            full_reply_chunks.append(chunk)
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"

        full_reply = "".join(full_reply_chunks).strip()

        # Save assistant message to database
        assistant_msg = AgentMessage(
            thread_id=thread.id,
            role="assistant",
            content=full_reply,
            proposed_fact=proposed_fact,
        )
        db.add(assistant_msg)
        await db.commit()
        await db.refresh(assistant_msg)

        if proposed_fact:
            yield f"data: {json.dumps({'proposed_fact': proposed_fact})}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
