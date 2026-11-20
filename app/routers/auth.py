
from datetime import datetime, timezone
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    hash_refresh_token,
    decode_token,
)
from app.database import get_session
from app.repositories import (
    user_repository,
    refresh_token_repository,
)
from app.schemas import RefreshToken


router = APIRouter(
    prefix="/auth",
    tags=["Autenticação"],
)



@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    user = await user_repository.get_user_by_email(
        session,
        form_data.username,
    )

    if user is None or not verify_password(
        form_data.password,
        user.password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": str(user.id)}
    )

    refresh_token = create_refresh_token(
        data={"sub": str(user.id)}
    )

    token_hash = hash_refresh_token(refresh_token)

    payload = decode_token(refresh_token)

    expires_at = datetime.fromtimestamp(
        payload["exp"],
        tz=timezone.utc,
    )

    await refresh_token_repository.create_refresh_token(
        session=session,
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )

    await session.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }



@router.post("/refresh")
async def refresh_access_token(
    token_data: RefreshToken,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Refresh token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token_data.refresh_token)

        if not isinstance(payload, dict):
            raise credentials_exception

        if payload.get("type") != "refresh":
            raise credentials_exception

        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

        user_id = int(user_id)

    except (jwt.InvalidTokenError, TypeError, ValueError):
        raise credentials_exception

    token_hash = hash_refresh_token(token_data.refresh_token)

    stored_token = await refresh_token_repository.get_refresh_token_by_hash_for_update(
        session,
        token_hash,
    )

    if stored_token is None:
        raise credentials_exception

    if stored_token.revoked:
        raise credentials_exception

    if stored_token.expires_at <= datetime.now(timezone.utc):
        raise credentials_exception

    if stored_token.user_id != user_id:
        raise credentials_exception

    user = await user_repository.get_user_by_id(
        session,
        user_id,
    )

    if user is None:
        raise credentials_exception

    try:
        await refresh_token_repository.revoke_refresh_token(
            session,
            stored_token,
        )

        access_token = create_access_token(
            data={"sub": str(user.id)}
        )

        new_refresh_token = create_refresh_token(
            data={"sub": str(user.id)}
        )

        new_payload = decode_token(new_refresh_token)

        new_expires_at = datetime.fromtimestamp(
            new_payload["exp"],
            tz=timezone.utc,
        )

        await refresh_token_repository.create_refresh_token(
            session=session,
            user_id=user.id,
            token_hash=hash_refresh_token(new_refresh_token),
            expires_at=new_expires_at,
        )

        await session.commit()

    except Exception:
        await session.rollback()
        raise

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }



@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    token_data: RefreshToken,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Refresh token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token_data.refresh_token)

        if not isinstance(payload, dict):
            raise credentials_exception

        if payload.get("type") != "refresh":
            raise credentials_exception

        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

        user_id = int(user_id)

    except (jwt.InvalidTokenError, TypeError, ValueError):
        raise credentials_exception

    token_hash = hash_refresh_token(token_data.refresh_token)

    stored_token = await refresh_token_repository.get_refresh_token_by_hash(
        session,
        token_hash,
    )

    if stored_token is None:
        raise credentials_exception

    if stored_token.revoked:
        raise credentials_exception

    if stored_token.expires_at <= datetime.now(timezone.utc):
        raise credentials_exception

    if stored_token.user_id != user_id:
        raise credentials_exception

    try:
        await refresh_token_repository.revoke_refresh_token(
            session,
            stored_token,
        )

        await session.commit()

    except Exception:
        await session.rollback()
        raise
