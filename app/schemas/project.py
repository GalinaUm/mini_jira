from pydantic import BaseModel, ConfigDict, Field
import uuid
from datetime import datetime


class ProjectBase(BaseModel):
    key: str = Field(..., max_length=10, description="Уникальный ключ проекта")
    name: str = Field(..., max_length=100)
    description: str | None = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    description: str | None = None


class ProjectResponse(ProjectBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)