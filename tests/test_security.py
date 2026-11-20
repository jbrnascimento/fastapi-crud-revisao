from app.core.security import (
    hash_password,
    verify_password,
)
from app.core.security import create_access_token
from app.database import settings
from datetime import datetime, timedelta, timezone
import pytest
import jwt

def test_hash_password():
    password = "MinhaSenha123"

    hashed_password = hash_password(password)

    assert hashed_password != password
    assert hashed_password.startswith("$argon2id$")


def test_verify_password_correct():
    password = "MinhaSenha123"

    hashed_password = hash_password(password)

    assert verify_password(password, hashed_password) is True


def test_verify_password_incorrect():
    password = "MinhaSenha123"

    hashed_password = hash_password(password)

    assert verify_password("SenhaErrada123", hashed_password) is False


def test_hash_password_generates_different_hashes():
    password = "MinhaSenha123"

    hash1 = hash_password(password)
    hash2 = hash_password(password)

    assert hash1 != hash2


def test_create_access_token():
    token = create_access_token({"sub": "15"})

    assert isinstance(token, str)
    assert len(token) > 0    


def test_decode_access_token():
    token = create_access_token({"sub": "15"})

    payload = jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.algorithm],
    )

    assert payload["sub"] == "15"
    assert "exp" in payload    


def test_decode_access_token_invalid_signature():
    token = create_access_token({"sub": "15"})

    with pytest.raises(jwt.InvalidSignatureError):
        jwt.decode(
            token,
            "X" * 32,
            algorithms=[settings.algorithm],
        )    


def test_decode_access_token_expired():
    expired_token = jwt.encode(
        {
            "sub": "15",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        settings.secret_key,
        algorithm=settings.algorithm,
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        jwt.decode(
            expired_token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )        