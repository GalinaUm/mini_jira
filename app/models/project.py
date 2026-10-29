import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Table, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.user import utcnow


project_members = Table(
    "project_members",
    Base.metadata,
    Column("project_id", Uuid, ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)

class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    key: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text, default=None)

    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    owner = relationship("User", foreign_keys=[owner_id], back_populates="owned_projects")
    members = relationship("User", secondary=project_members, back_populates=None, lazy="selectin",)
    tasks = relationship(
        "Task",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin"
    )
