import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.access import get_project_for_user, get_project_for_owner
from app.database import get_db
from app.models.user import User
from app.models.project import Project
from app.schemas.project import ProjectResponse, ProjectCreate, ProjectUpdate, ProjectMemberAdd
from app.schemas.user import UserResponse
from app.deps import get_current_user
from app.access import get_project_for_owner, get_project_for_user


router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_in: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing_project = await db.scalar(select(Project).where(Project.key == project_in.key))
    if existing_project:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Проект с таким ключом (key) уже существует"
        )
    new_project = Project(
        **project_in.model_dump(),
        owner_id=current_user.id
    )
    new_project.members.append(current_user)
    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)
    return new_project


@router.get("/", response_model=list[ProjectResponse], status_code=status.HTTP_200_OK)
async def get_projects(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.scalars(
        select(Project).where(
            (Project.owner_id == current_user.id) |
            (Project.members.contains(current_user))
        )
    )
    projects = result.unique().all()

    return projects


@router.get("/{project_id}", response_model=ProjectResponse, status_code=status.HTTP_200_OK)
async def get_project(
        project_id: uuid.UUID,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    return await get_project_for_user(db, project_id, current_user)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
        project_id: uuid.UUID,
        project_in: ProjectUpdate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    project = await get_project_for_owner(db, project_id, current_user)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Проект не найден")
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Только владелец может редактировать проект)")
    update_data = project_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)

    await db.commit()
    await db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = await get_project_for_owner(db, project_id, current_user)

    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Проект не найден")
    await db.delete(project)
    await db.commit()
    return None


@router.get("/{project_id}/members", response_model=list[UserResponse])
async def list_project_members(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = await get_project_for_user(db, project_id, current_user)
    return project.members


@router.post(
    "/{project_id}/members",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_project_member(
    project_id: uuid.UUID,
    member_in: ProjectMemberAdd,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = await get_project_for_owner(db, project_id, current_user)

    user = await db.scalar(
        select(User).where(User.email == member_in.email)
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь с таким email не найден",
        )
    if user.id == project.owner_id or any(
        member.id == user.id for member in project.members
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь уже является участником проекта",
        )
    project.members.append(user)
    await db.commit()
    return user


@router.delete(
    "/{project_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_project_member(
        project_id: uuid.UUID,
        user_id: uuid.UUID,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    project = await get_project_for_owner(db, project_id, current_user)

    if user_id == project.owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя удалить владельца проекта",
        )

    member = next(
        (m for m in project.members if m.id == user_id),
        None,
    )
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не является участником проекта",
        )

    project.members.remove(member)
    await db.commit()
    return None


