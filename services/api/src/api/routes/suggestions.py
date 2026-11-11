import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from api.db import get_db
from api.models.conversation import Conversation, Suggestion
from api.models.user import User
from api.schemas.conversation import SuggestionResponse, SuggestionUpdate

router = APIRouter(prefix="/v1/suggestions", tags=["suggestions"])


@router.patch("/{suggestion_id}", response_model=SuggestionResponse)
async def update_suggestion(
    suggestion_id: uuid.UUID,
    payload: SuggestionUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Suggestion:
    # Join conversation to check user ownership
    stmt = (
        select(Suggestion)
        .join(Conversation, Suggestion.conversation_id == Conversation.id)
        .where(
            Suggestion.id == suggestion_id,
            Conversation.user_id == current_user.id,
        )
    )
    result = await db.execute(stmt)
    suggestion = result.scalar_one_or_none()
    if not suggestion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Suggestion not found",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(suggestion, field, value)

    await db.commit()
    await db.refresh(suggestion)
    return suggestion
