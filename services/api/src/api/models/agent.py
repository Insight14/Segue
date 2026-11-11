import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.models.base import Base

if TYPE_CHECKING:
    from api.models.user import User


class AgentThread(Base):
    __tablename__ = "agent_threads"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    mode: Mapped[str] = mapped_column(String(50), nullable=False)  # "discover" | "prep"
    title: Mapped[str] = mapped_column(String(255), default="New Thread", nullable=False)

    user: Mapped["User"] = relationship("User")
    messages: Mapped[list["AgentMessage"]] = relationship(
        "AgentMessage",
        back_populates="thread",
        cascade="all, delete-orphan",
        order_by="AgentMessage.created_at",
    )


class AgentMessage(Base):
    __tablename__ = "agent_messages"

    thread_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agent_threads.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # "user" | "assistant" | "system"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    proposed_fact: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    thread: Mapped["AgentThread"] = relationship("AgentThread", back_populates="messages")
