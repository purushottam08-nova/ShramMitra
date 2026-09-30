from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class SchemeState(Base):
    __tablename__ = "scheme_states"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    scheme_id: Mapped[int] = mapped_column(
        ForeignKey("schemes.id"),
        nullable=False,
    )

    state_id: Mapped[int] = mapped_column(
        ForeignKey("states.id"),
        nullable=False,
    )