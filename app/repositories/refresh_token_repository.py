
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RefreshToken


async def create_refresh_token(
    session: AsyncSession,
    user_id: int,
    token_hash: str,
    expires_at: datetime,
) -> RefreshToken:

    refresh_token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
    )

    session.add(refresh_token)
    await session.flush()

    return refresh_token


async def get_refresh_token_by_hash(
    session: AsyncSession,
    token_hash: str,
) -> RefreshToken | None:

    result = await session.scalars(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash
        )
    )

    return result.first()


async def get_refresh_token_by_hash_for_update(
    session: AsyncSession,
    token_hash: str,
) -> RefreshToken | None:

    result = await session.scalars(
        select(RefreshToken)
        .where(
            RefreshToken.token_hash == token_hash
        )
        .with_for_update()
    )

    return result.first()


async def revoke_refresh_token(
    session: AsyncSession,
    refresh_token: RefreshToken,
) -> None:

    refresh_token.revoked = True

    await session.flush()
