
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models import User
from app.repositories import user_repository
from app.services.exceptions import (
    UserNotFoundError,
    UserEmailAlreadyExistsError,
)
from app.core.security import hash_password


def _is_email_unique_violation(exc: IntegrityError) -> bool:
    original = exc.orig
    diagnostic = getattr(original, "diag", None)

    return (
        getattr(diagnostic, "constraint_name", None)
        == "users_email_key"
    )


async def create_user(
    session: AsyncSession,
    user_data: dict,
) -> User:
    existing_user = await user_repository.get_user_by_email(
        session,
        user_data["email"],
    )

    if existing_user is not None:
        raise UserEmailAlreadyExistsError(
            "Este e-mail já está cadastrado"
        )

    try:
        user_data["password"] = hash_password(user_data["password"])

        user = await user_repository.create_user(
            session,
            user_data,
        )

        await session.commit()
        await session.refresh(user)

        return user

    except IntegrityError as exc:
        await session.rollback()

        if _is_email_unique_violation(exc):
            raise UserEmailAlreadyExistsError(
                "Este e-mail já está cadastrado"
            ) from exc

        raise

    except Exception:
        await session.rollback()
        raise


async def get_user(
    session: AsyncSession,
    user_id: int,
) -> User:
    user = await user_repository.get_user_by_id(
        session,
        user_id,
    )

    if user is None:
        raise UserNotFoundError("Usuário não encontrado")

    return user


async def get_all_users(
    session: AsyncSession,
) -> list[User]:
    return await user_repository.get_all_users(session)


async def update_user(
    session: AsyncSession,
    user_id: int,
    update_data: dict,
) -> User:

    user = await get_user(session, user_id)

    if "email" in update_data:
        existing_user = await user_repository.get_user_by_email(
            session,
            update_data["email"],
        )

        if existing_user is not None and existing_user.id != user.id:
            raise UserEmailAlreadyExistsError(
                "Este e-mail já está cadastrado"
            )

    try:
        await user_repository.update_user(
            session,
            user,
            update_data,
        )

        await session.commit()
        await session.refresh(user)

        return user

    except IntegrityError as exc:
        await session.rollback()

        if _is_email_unique_violation(exc):
            raise UserEmailAlreadyExistsError(
                "Este e-mail já está cadastrado"
            ) from exc

        raise

    except Exception:
        await session.rollback()
        raise


async def delete_user(
    session: AsyncSession,
    user_id: int,
) -> None:
    user = await get_user(session, user_id)

    try:
        await user_repository.delete_user(session, user)
        await session.commit()

    except Exception:
        await session.rollback()
        raise
