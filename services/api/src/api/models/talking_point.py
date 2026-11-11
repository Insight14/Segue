import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.models.base import Base

if TYPE_CHECKING:
    from api.models.user import User


class TalkingPoint(Base):
    __tablename__ = "talking_points"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    event_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    contact_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    content: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    user: Mapped["User"] = relationship("User")
