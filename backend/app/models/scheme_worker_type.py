from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class SchemeWorkerType(Base):
    __tablename__ = "scheme_worker_types"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    scheme_id: Mapped[int] = mapped_column(
        ForeignKey("schemes.id"),
        nullable=False,
    )

    worker_type_id: Mapped[int] = mapped_column(
        ForeignKey("worker_types.id"),
        nullable=False,
    )