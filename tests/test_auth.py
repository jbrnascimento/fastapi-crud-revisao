
import pytest
from fastapi import HTTPException

from app.core.auth import get_current_user
from app.core.security import create_access_token


@pytest.mark.anyio
async def test_get_current_user_success(user, test_session):
    token = create_access_token(
        data={"sub": str(user["id"])}
    )

    current_user = await get_current_user(
        token=token,
        session=test_session,
    )

    assert current_user.id == user["id"]
    assert current_user.email == user["email"]


@pytest.mark.anyio
async def test_get_current_user_invalid_token(test_session):
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(
            token="token_invalido",
            session=test_session,
        )

    assert exc_info.value.status_code == 401


@pytest.mark.anyio
async def test_get_current_user_nonexistent_user(test_session):
    token = create_access_token(
        data={"sub": "999999"}
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(
            token=token,
            session=test_session,
        )

    assert exc_info.value.status_code == 401
