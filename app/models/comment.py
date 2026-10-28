import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.user import utcnow


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), index=True, nullable=False
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    task = relationship("Task", back_populates="comments")
    author = relationship("User", back_populates="comments")