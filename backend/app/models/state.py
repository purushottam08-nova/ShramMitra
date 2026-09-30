from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class State(Base):
    __tablename__ = "states"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    code: Mapped[str] = mapped_column(
        String(10),
        unique=True,
        nullable=False,
    )