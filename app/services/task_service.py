
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Task
from app.repositories import task_repository
from app.services.exceptions import TaskNotFoundError


async def create_task(
    session: AsyncSession,
    task_data: dict,
    user_id: int,
) -> Task:
    try:
        task_data["user_id"] = user_id

        task = await task_repository.create_task(
            session,
            task_data,
        )

        await session.commit()
        await session.refresh(task)

        return task

    except Exception:
        await session.rollback()
        raise


async def get_task(
    session: AsyncSession,
    task_id: int,
    user_id: int,
) -> Task:
    task = await task_repository.get_task_by_id(
        session,
        task_id,
        user_id,
    )

    if task is None:
        raise TaskNotFoundError("Tarefa não encontrada")

    return task


async def get_all_tasks(
    session: AsyncSession,
    user_id: int,
) -> list[Task]:
    return await task_repository.get_all_tasks(
        session,
        user_id,
    )


async def update_task(
    session: AsyncSession,
    task_id: int,
    user_id: int,
    update_data: dict,
) -> Task:
    task = await get_task(session, task_id, user_id)

    try:
        await task_repository.update_task(
            session,
            task,
            update_data,
        )

        await session.commit()
        await session.refresh(task)

        return task

    except Exception:
        await session.rollback()
        raise


async def delete_task(
    session: AsyncSession,
    task_id: int,
    user_id: int,
) -> None:
    task = await get_task(session, task_id, user_id)

    try:
        await task_repository.delete_task(
            session,
            task,
        )

        await session.commit()

    except Exception:
        await session.rollback()
        raise
