
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas import UserCreate, UserPublic, UserUpdate
from app.services import user_service
from app.services.exceptions import (
    UserNotFoundError,
    UserEmailAlreadyExistsError,
)


router = APIRouter(prefix="/users", tags=["Usuários"])


@router.post(
    "",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    user_data: UserCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    try:
        return await user_service.create_user(
            session,
            user_data.model_dump(),
        )
    except UserEmailAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get("", response_model=list[UserPublic])
async def list_users(
    session: Annotated[AsyncSession, Depends(get_session)],
):
    return await user_service.get_all_users(session)


@router.get("/{user_id}", response_model=UserPublic)
async def get_user(
    user_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    try:
        return await user_service.get_user(session, user_id)
    except UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.patch("/{user_id}", response_model=UserPublic)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    try:
        return await user_service.update_user(
            session,
            user_id,
            user_data.model_dump(exclude_unset=True),
        )
    except UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except UserEmailAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user(
    user_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    try:
        await user_service.delete_user(session, user_id)
    except UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
