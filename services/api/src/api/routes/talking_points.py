import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.agent.prep import generate_talking_points_for_user
from api.auth import get_current_user
from api.db import get_db_session
from api.models.fact import ProfileFact
from api.models.profile import Profile
from api.models.talking_point import TalkingPoint
from api.models.user import User
from api.schemas.agent import GenerateTalkingPointsRequest, TalkingPointsResponse

router = APIRouter(prefix="/v1/talking-points", tags=["talking-points"])


@router.post("", response_model=TalkingPointsResponse, status_code=status.HTTP_201_CREATED)
async def create_talking_points(
    payload: GenerateTalkingPointsRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TalkingPoint:
    """Generate structured talking points for the authenticated user."""
    # 1. Fetch user's profile
    prof_res = await db.execute(select(Profile).where(Profile.user_id == user.id))
    profile = prof_res.scalar_one_or_none()

    # 2. Fetch user's CONFIRMED facts only
    facts_res = await db.execute(
        select(ProfileFact).where(
            ProfileFact.user_id == user.id,
            ProfileFact.confirmed.is_(True),
        )
    )
    confirmed_facts = list(facts_res.scalars().all())

    # 3. Generate talking points using Prep logic
    content = await generate_talking_points_for_user(
        profile=profile,
        confirmed_facts=confirmed_facts,
        notes=payload.notes,
    )

    # 4. Save talking points to database
    talking_point = TalkingPoint(
        user_id=user.id,
        event_id=payload.event_id,
        contact_id=payload.contact_id,
        content=content.model_dump(),
    )
    db.add(talking_point)
    await db.commit()
    await db.refresh(talking_point)
    return talking_point


@router.get("/{id}", response_model=TalkingPointsResponse, status_code=status.HTTP_200_OK)
async def get_talking_point(
    id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TalkingPoint:
    """Retrieve talking points by ID (strictly isolated to owner)."""
    stmt = select(TalkingPoint).where(TalkingPoint.id == id, TalkingPoint.user_id == user.id)
    result = await db.execute(stmt)
    tp = result.scalar_one_or_none()
    if not tp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Talking points not found"
        )
    return tp


@router.get("", response_model=list[TalkingPointsResponse], status_code=status.HTTP_200_OK)
async def list_talking_points(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[TalkingPoint]:
    """List all saved talking points for the authenticated user."""
    stmt = (
        select(TalkingPoint)
        .where(TalkingPoint.user_id == user.id)
        .order_by(TalkingPoint.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
