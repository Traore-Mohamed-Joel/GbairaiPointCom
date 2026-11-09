from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
    Index,
)

from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


# Interdit les noms identiques, sans tenir compte des majuscules.
Index(
    "uq_groups_name_lower",
    func.lower(Group.name),
    unique=True,
)