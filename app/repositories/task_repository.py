
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Task


async def get_task_by_id(
    session: AsyncSession,
    task_id: int,
    user_id: int,
) -> Task | None:
    result = await session.scalars(
        select(Task).where(
            Task.id == task_id,
            Task.user_id == user_id,
        )
    )

    return result.first()


async def get_all_tasks(
    session: AsyncSession,
    user_id: int,
) -> list[Task]:
    result = await session.scalars(
        select(Task).where(Task.user_id == user_id)
    )

    return result.all()


async def create_task(
    session: AsyncSession,
    task_data: dict,
) -> Task:
    task = Task(**task_data)

    session.add(task)
    await session.flush()

    return task


async def update_task(
    session: AsyncSession,
    task: Task,
    update_data: dict,
) -> Task:

    for field, value in update_data.items():
        setattr(task, field, value)

    await session.flush()

    return task


async def delete_task(
    session: AsyncSession,
    task: Task,
) -> None:
    await session.delete(task)
    await session.flush()
