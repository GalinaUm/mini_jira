import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str | None] = mapped_column(String(120), default=None)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    owned_projects = relationship("Project", foreign_keys="Project.owner_id", back_populates="owner")
    assignee_tasks = relationship("Task", foreign_keys="Task.assignee_id", back_populates="assignee")
    created_tasks = relationship("Task", foreign_keys="Task.created_by_id", back_populates="created_by")
    comments = relationship("Comment", back_populates="author")