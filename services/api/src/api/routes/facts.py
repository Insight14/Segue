import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from api.db import get_db_session
from api.models.fact import ProfileFact
from api.models.user import User
from api.schemas.fact import FactCreate, FactKind, FactResponse, FactUpdate

router = APIRouter(prefix="/v1/facts", tags=["facts"])


@router.get("", response_model=list[FactResponse], status_code=status.HTTP_200_OK)
async def list_facts(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    kind: Annotated[FactKind | None, Query(description="Filter by fact kind")] = None,
    confirmed: Annotated[bool | None, Query(description="Filter by confirmation status")] = None,
    tag: Annotated[str | None, Query(description="Filter by tag")] = None,
) -> list[ProfileFact]:
    """List all profile facts belonging to the authenticated user."""
    stmt = select(ProfileFact).where(ProfileFact.user_id == user.id)

    if kind is not None:
        stmt = stmt.where(ProfileFact.kind == kind.value)
    if confirmed is not None:
        stmt = stmt.where(ProfileFact.confirmed == confirmed)

    stmt = stmt.order_by(ProfileFact.created_at.desc())
    result = await db.execute(stmt)
    facts = list(result.scalars().all())

    # In-memory filter for tags if specified (ensures cross-database consistency)
    if tag is not None:
        facts = [f for f in facts if tag in (f.tags or [])]

    return facts


@router.post("", response_model=FactResponse, status_code=status.HTTP_201_CREATED)
async def create_fact(
    payload: FactCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ProfileFact:
    """Create a new fact for the authenticated user."""
    fact = ProfileFact(
        user_id=user.id,
        kind=payload.kind.value,
        title=payload.title,
        body=payload.body,
        tags=payload.tags,
        source=payload.source.value,
        confirmed=payload.confirmed,
    )
    db.add(fact)
    await db.commit()
    await db.refresh(fact)
    return fact


@router.patch("/{fact_id}", response_model=FactResponse, status_code=status.HTTP_200_OK)
async def update_fact(
    fact_id: uuid.UUID,
    payload: FactUpdate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ProfileFact:
    """Update a specific fact owned by the authenticated user."""
    # Strict isolation: filter by both fact_id AND user_id
    stmt = select(ProfileFact).where(
        ProfileFact.id == fact_id,
        ProfileFact.user_id == user.id,
    )
    result = await db.execute(stmt)
    fact = result.scalar_one_or_none()

    if not fact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fact not found",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "kind" and value is not None:
            fact.kind = value.value if hasattr(value, "value") else str(value)
        else:
            setattr(fact, field, value)

    await db.commit()
    await db.refresh(fact)
    return fact


@router.delete("/{fact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fact(
    fact_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    """Delete a fact owned by the authenticated user."""
    # Strict isolation: filter by both fact_id AND user_id
    stmt = select(ProfileFact).where(
        ProfileFact.id == fact_id,
        ProfileFact.user_id == user.id,
    )
    result = await db.execute(stmt)
    fact = result.scalar_one_or_none()

    if not fact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fact not found",
        )

    await db.delete(fact)
    await db.commit()
