
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session, settings
from app.models import User
from app.repositories import user_repository


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/token"
)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )

        if not isinstance(payload, dict):
            raise credentials_exception

        token_type = payload.get("type")

        if token_type != "access":
            raise credentials_exception

        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

        user_id = int(user_id)

    except (jwt.InvalidTokenError, TypeError, ValueError):
        raise credentials_exception

    user = await user_repository.get_user_by_id(
        session,
        user_id,
    )

    if user is None:
        raise credentials_exception

    return user
