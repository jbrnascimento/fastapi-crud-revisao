
import pytest

from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)

from app.database import settings, get_session
from app.main import app
from app.models import Base


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def test_engine(anyio_backend):
    test_url = make_url(settings.database_url).set(
        database="Treinamento_test"
    )

    engine = create_async_engine(
        test_url,
        connect_args={
            "server_settings": {
                "search_path": "fastapi_crud"
            }
        },
    )

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
def concurrent_session_factory(test_engine):
    return async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest.fixture
async def test_session(test_engine):
    async with test_engine.connect() as connection:
        transaction = await connection.begin()

        TestingSessionLocal = async_sessionmaker(
            bind=connection,
            class_=AsyncSession,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )

        try:
            async with TestingSessionLocal() as session:
                yield session
        finally:
            await transaction.rollback()


@pytest.fixture
async def client(test_session):
    async def override_get_session():
        yield test_session

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as test_client:
        yield test_client

    app.dependency_overrides.pop(get_session, None)



@pytest.fixture
async def concurrent_client(test_engine):
    TestingSessionLocal = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def override_get_session():
        async with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as test_client:
        yield test_client

    app.dependency_overrides.pop(get_session, None)


@pytest.fixture
async def user(client):
    response = await client.post(
        "/users",
        json={
            "name": "Usuário de teste",
            "email": "usuario.teste@example.com",
            "password": "SenhaTeste123",
        },
    )

    assert response.status_code == 201

    return response.json()


@pytest.fixture
async def authenticated_client(client, user):
    response = await client.post(
        "/auth/token",
        data={
            "username": user["email"],
            "password": "SenhaTeste123",
        },
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    client.headers.update({
        "Authorization": f"Bearer {token}"
    })

    return client
