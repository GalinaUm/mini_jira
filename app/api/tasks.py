import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.access import (
    ensure_user_is_member,
    get_project_for_user,
    get_task_for_user
)
from app.database import get_db
from app.deps import get_current_user
from app.models.project import Project
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse, TaskMove

router = APIRouter(tags=["tasks"])


@router.post(
    "/projects/{project_id}/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    project_id: uuid.UUID,
    task_in: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = await get_project_for_user(db, project_id, current_user)

    if task_in.assignee_id is not None:
        await ensure_user_is_member(db, project, task_in.assignee_id,)

    max_position = await db.scalar(
        select(func.coalesce(func.max(Task.position), -1)).where(
            Task.project_id == project.id,
            Task.status == task_in.status,
        )
    )

    next_position = (max_position if max_position is not None else -1) + 1

    task = Task(
        project_id=project.id,
        title=task_in.title,
        description=task_in.description,
        status=task_in.status,
        priority=task_in.priority,
        assignee_id=task_in.assignee_id,
        due_date=task_in.due_date,
        created_by_id=current_user.id,
        position=next_position,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.get(
    "/projects/{project_id}/tasks",
    response_model=list[TaskResponse],
)
async def list_tasks(
    project_id: uuid.UUID,
    status_filter: TaskStatus | None = Query(default=None, alias="status"),
    assignee_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = await get_project_for_user(db, project_id, current_user)

    query = select(Task).where(Task.project_id == project.id)

    if status_filter is not None:
        query = query.where(Task.status == status_filter)

    if assignee_id is not None:
        query = query.where(Task.assignee_id == assignee_id)

    query = query.order_by(
        Task.status,
        Task.position,
        Task.created_at,
    )
    result = await db.scalars(query)

    return list(result.all())


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task, _ = await get_task_for_user(db, task_id, current_user)
    return task


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: uuid.UUID,
    task_in: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task, project = await get_task_for_user(db, task_id, current_user)

    data = task_in.model_dump(exclude_unset=True)

    if "assignee" in data and data["assignee_id"] is not None:
        await ensure_user_is_member(db, project, data["assignee_id"])

    for field, value in data.items():
        setattr(task, field, value)

    await db.commit()
    await db.refresh(task)
    return task


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task, project = await get_task_for_user(db, task_id, current_user)

    if (
        task.created_by_id != current_user.id
        and project.owner_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Удалять задачу может автор или владелец проекта",
        )
    await db.delete(task)
    await db.commit()
    return None


@router.patch("/tasks/{task_id}/move", response_model=TaskResponse)
async def move_task(
    task_id: uuid.UUID,
    move: TaskMove,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task, _ = await get_task_for_user(db, task_id, current_user)

    statuses =[task.status]
    if move.status != task.status:
        statuses.append(move.status)

    result = await db.scalar(
        select(Task).where(
            Task.project_id == task.project_id,
            Task.status.in_(statuses),
        )
        .order_by(Task.status, Task.position, Task.created_at)
        .with_for_update()
    )
    rows = list(result.all())

    columns: dict[TaskStatus, list[Task]] = {
        task_status: [] for task_status in statuses
    }

    for row in rows:
        columns[row.status].append(row)

    source = columns[task.status]
    source.remove(task)

    target = (
        source
        if task.status == move.status
        else columns[move.status]
    )

    target.insert(min(move.position, len(target)), task)
    task.status = move.status

    for column in columns.values():
        for index, row in enumerate(column):
            row.position = index

    await db.commit()
    await db.refresh(task)
    return task
















