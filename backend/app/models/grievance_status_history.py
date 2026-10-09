
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class GrievanceStatusHistory(Base):
    __tablename__ = "grievance_status_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    grievance_id: Mapped[int] = mapped_column(
        ForeignKey("grievances.id"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    changed_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    grievance = relationship(
        "Grievance",
        back_populates="status_history",
    )