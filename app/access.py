import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project, project_members
from app.models.user import User


async def get_project_for_user(
        db: AsyncSession,
        project_id: uuid.UUID,
        user: User,
) -> Project:
    project = await db.scalar(
        select(Project).where(Project.id == project_id)
    )
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Project not found')
    if project.owner_id == user.id:
        return project

    member_id = await db.scalar(
        select(project_members.c.user_id).where(
        project_members.c.project_id == project_id,
        project_members.c.user_id == user.id
    )
)
    if member_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Member not found')

    return project


async def get_project_for_owner(
        db: AsyncSession,
        project_id: uuid.UUID,
        user: User,
) -> Project:
    project = await get_project_for_user(db, project_id, user)
    if project.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только владелец проекта может выполнить это действие",
        )
    return project


async def ensure_user_is_member(
        db: AsyncSession,
        project: Project,
        user_id: uuid.UUID,
) -> None:
    if user_id == project.owner_id:
        return

    member_id = await db.scalar(
        select(project_members.c.user_id).where(
            project_members.c.project_id == project.id,
            project_members.c.user_id == user_id,
        )
    )
    if member_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь не является участником проекта",
        )

