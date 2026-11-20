
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import User
from app.schemas import TaskCreate, TaskPublic, TaskUpdate
from app.services import task_service
from app.core.auth import get_current_user


router = APIRouter(
    prefix="/tasks",
    tags=["Tarefas"],
)


@router.post(
    "",
    response_model=TaskPublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    task_data: TaskCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await task_service.create_task(
        session,
        task_data.model_dump(),
        current_user.id,
    )


@router.get("", response_model=list[TaskPublic])
async def list_tasks(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await task_service.get_all_tasks(
        session,
        current_user.id,
    )


@router.get("/{task_id}", response_model=TaskPublic)
async def get_task(
    task_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await task_service.get_task(
        session,
        task_id,
        current_user.id,
    )


@router.patch("/{task_id}", response_model=TaskPublic)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await task_service.update_task(
        session,
        task_id,
        current_user.id,
        task_data.model_dump(exclude_unset=True),
    )


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_task(
    task_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await task_service.delete_task(
        session,
        task_id,
        current_user.id,
    )
