from sqlalchemy import (
    String,
    Boolean,
    ForeignKey,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255)
    )

    todos: Mapped[list["Todo"]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
    )


class Todo(Base):
    __tablename__ = "todos"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    title: Mapped[str] = mapped_column(
        String(200)
    )

    completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    owner: Mapped["User"] = relationship(
        back_populates="todos"
    )