from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class SchemeRule(Base):
    __tablename__ = "scheme_rules"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    scheme_id: Mapped[int] = mapped_column(
        ForeignKey("schemes.id"),
        nullable=False,
    )

    field: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    operator: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    value: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    logical_group: Mapped[int] = mapped_column(
        default=1,
        nullable=False,
    )

    logical_operator: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="AND",
    )