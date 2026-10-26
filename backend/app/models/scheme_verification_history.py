
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class SchemeVerificationHistory(Base):
    __tablename__ = "scheme_verification_history"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    scheme_id: Mapped[int] = mapped_column(
        ForeignKey("schemes.id"),
        nullable=False,
        index=True,
    )

    verifier_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    previous_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    new_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    source_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    version: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    notes: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    verified_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    scheme = relationship("Scheme")
    verifier = relationship("User")
