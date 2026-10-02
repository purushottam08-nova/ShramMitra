from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class WorkerProfile(Base):
    __tablename__ = "worker_profiles"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
    )

    state: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    district: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    worker_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    employment_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    monthly_income_range: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    age: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    monthly_income: Mapped[float | None] = mapped_column(
        nullable=True,
    )

    epfo_status: Mapped[bool | None] = mapped_column(
        nullable=True,
    )

    esic_status: Mapped[bool | None] = mapped_column(
        nullable=True,
    )

    nps_status: Mapped[bool | None] = mapped_column(
        nullable=True,
    )

    income_tax_payer: Mapped[bool | None] = mapped_column(
        nullable=True,
    )

    user = relationship("User", back_populates="worker_profile")