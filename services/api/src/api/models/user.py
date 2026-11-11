from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.models.base import Base

if TYPE_CHECKING:
    from api.models.document import Document
    from api.models.fact import ProfileFact
    from api.models.profile import Profile


class User(Base):
    __tablename__ = "users"

    cognito_sub: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    retention_days: Mapped[int | None] = mapped_column(Integer, nullable=True, default=90)
    settings: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    profile: Mapped["Profile | None"] = relationship(
        "Profile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    facts: Mapped[list["ProfileFact"]] = relationship(
        "ProfileFact",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    documents: Mapped[list["Document"]] = relationship(
        "Document",
        back_populates="user",
        cascade="all, delete-orphan",
    )
