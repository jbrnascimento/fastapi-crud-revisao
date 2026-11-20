
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


async def get_user_by_id(
    session: AsyncSession,
    user_id: int,
) -> User | None:
    result = await session.scalars(
        select(User).where(User.id == user_id)
    )

    return result.first()


async def get_user_by_email(
    session: AsyncSession,
    email: str,
) -> User | None:
    result = await session.scalars(
        select(User).where(User.email == email)
    )

    return result.first()


async def get_all_users(
    session: AsyncSession,
) -> list[User]:
    result = await session.scalars(select(User))
    return result.all()


async def create_user(
    session: AsyncSession,
    user_data: dict,
) -> User:
    user = User(**user_data)

    session.add(user)
    await session.flush()

    return user


async def update_user(
    session: AsyncSession,
    user: User,
    update_data: dict,
) -> User:

    for field, value in update_data.items():
        setattr(user, field, value)

    await session.flush()

    return user


async def delete_user(
    session: AsyncSession,
    user: User,
) -> None:
    await session.delete(user)
    await session.flush()
