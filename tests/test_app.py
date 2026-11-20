import asyncio
import uuid
import jwt
import pytest

from datetime import datetime, timedelta, timezone

from sqlalchemy import select, text

from app.models import User
from app.database import settings
from app.repositories import refresh_token_repository
from app.core.security import (
    create_refresh_token,
    hash_refresh_token,
    verify_password,
)

from types import SimpleNamespace
from app.routers import celery_tasks

# =====================================================
# TESTES DE CONEXÃO E ROTAS PÚBLICAS
# =====================================================

@pytest.mark.anyio
async def test_database_connection(test_engine):
    async with test_engine.connect() as connection:
        result = await connection.execute(
            text("""
                SELECT
                    current_database(),
                    current_schema()
            """)
        )

        database, schema = result.one()

        assert database == "Treinamento_test"
        assert schema == "fastapi_crud"


@pytest.mark.anyio
async def test_read_root(client):
    response = await client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "API de tarefas funcionando"
    }


@pytest.mark.anyio
async def test_create_task(authenticated_client):
    response = await authenticated_client.post(
        "/tasks",
        json={
            "title": "Estudar FastAPI",
            "description": "Revisar CRUD assíncrono",
            "done": False,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "Estudar FastAPI"
    assert data["description"] == "Revisar CRUD assíncrono"
    assert data["done"] is False


@pytest.mark.anyio
async def test_list_tasks(authenticated_client):
    await authenticated_client.post(
        "/tasks",
        json={
            "title": "Primeira tarefa",
            "description": "Descrição",
            "done": False,
        },
    )

    response = await authenticated_client.get("/tasks")

    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.anyio
async def test_get_task(authenticated_client):
    create_response = await authenticated_client.post(
        "/tasks",
        json={
            "title": "Buscar tarefa",
            "description": "Teste de consulta",
            "done": False,
        },
    )

    task_id = create_response.json()["id"]

    response = await authenticated_client.get(f"/tasks/{task_id}")

    assert response.status_code == 200
    assert response.json()["id"] == task_id


@pytest.mark.anyio
async def test_get_task_not_found(authenticated_client):
    response = await authenticated_client.get("/tasks/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Tarefa não encontrada"



# =====================================================
# TESTES DE ATUALIZAÇÃO E EXCLUSÃO DE TASKS
# =====================================================

@pytest.mark.anyio
async def test_update_task(authenticated_client):
    create_response = await authenticated_client.post(
        "/tasks",
        json={
            "title": "Estudar pytest",
            "description": "Descrição original",
            "done": False,
        },
    )

    task_id = create_response.json()["id"]

    response = await authenticated_client.patch(
        f"/tasks/{task_id}",
        json={"done": True},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == task_id
    assert data["title"] == "Estudar pytest"
    assert data["description"] == "Descrição original"
    assert data["done"] is True


@pytest.mark.anyio
async def test_update_task_not_found(authenticated_client):
    response = await authenticated_client.patch(
        "/tasks/999999",
        json={"done": True},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Tarefa não encontrada"
    }


@pytest.mark.anyio
async def test_delete_task(authenticated_client):
    create_response = await authenticated_client.post(
        "/tasks",
        json={
            "title": "Excluir esta tarefa",
            "description": "Teste de DELETE",
            "done": False,
        },
    )

    task_id = create_response.json()["id"]

    response = await authenticated_client.delete(
        f"/tasks/{task_id}"
    )

    assert response.status_code == 204

    get_response = await authenticated_client.get(
        f"/tasks/{task_id}"
    )

    assert get_response.status_code == 404


@pytest.mark.anyio
async def test_delete_task_not_found(authenticated_client):
    response = await authenticated_client.delete("/tasks/999999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Tarefa não encontrada"
    }


# =====================================================
# TESTES DE VALIDAÇÃO DE TASKS
# =====================================================

@pytest.mark.anyio
async def test_create_task_empty_title(authenticated_client):
    response = await authenticated_client.post(
        "/tasks",
        json={
            "title": "",
            "description": "Título inválido",
            "done": False,
        },
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_update_task_empty_payload(authenticated_client):
    create_response = await authenticated_client.post(
        "/tasks",
        json={
            "title": "Tarefa válida",
            "description": None,
            "done": False,
        },
    )

    task_id = create_response.json()["id"]

    response = await authenticated_client.patch(
        f"/tasks/{task_id}",
        json={},
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_task_with_null_description(authenticated_client):
    response = await authenticated_client.post(
        "/tasks",
        json={
            "title": "Estudar Pydantic",
            "description": None,
            "done": False,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "Estudar Pydantic"
    assert data["description"] is None
    assert data["done"] is False


@pytest.mark.anyio
async def test_update_task_only_title(authenticated_client):
    create_response = await authenticated_client.post(
        "/tasks",
        json={
            "title": "Título original",
            "description": "Descrição que deve permanecer",
            "done": False,
        },
    )

    task_id = create_response.json()["id"]

    response = await authenticated_client.patch(
        f"/tasks/{task_id}",
        json={"title": "Título atualizado"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "Título atualizado"
    assert data["description"] == "Descrição que deve permanecer"
    assert data["done"] is False


@pytest.mark.anyio
async def test_update_task_title_null(authenticated_client):
    create_response = await authenticated_client.post(
        "/tasks",
        json={
            "title": "Estudar FastAPI",
            "description": "Revisar validações",
            "done": False,
        },
    )

    task_id = create_response.json()["id"]

    response = await authenticated_client.patch(
        f"/tasks/{task_id}",
        json={"title": None},
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_update_task_done_null(authenticated_client):
    create_response = await authenticated_client.post(
        "/tasks",
        json={
            "title": "Estudar SQLAlchemy",
            "description": "Praticar atualizações",
            "done": False,
        },
    )

    task_id = create_response.json()["id"]

    response = await authenticated_client.patch(
        f"/tasks/{task_id}",
        json={"done": None},
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_task_title_only_spaces(authenticated_client):
    response = await authenticated_client.post(
        "/tasks",
        json={
            "title": "     ",
            "description": "Título inválido",
            "done": False,
        },
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_update_task_title_only_spaces(authenticated_client):
    create_response = await authenticated_client.post(
        "/tasks",
        json={
            "title": "Estudar Python",
            "description": "Teste de atualização",
            "done": False,
        },
    )

    task_id = create_response.json()["id"]

    response = await authenticated_client.patch(
        f"/tasks/{task_id}",
        json={"title": "     "},
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_task_title_strip(authenticated_client):
    response = await authenticated_client.post(
        "/tasks",
        json={
            "title": "  Estudar Python  ",
            "description": "Teste de normalização",
            "done": False,
        },
    )

    assert response.status_code == 201
    assert response.json()["title"] == "Estudar Python"


@pytest.mark.anyio
async def test_update_task_title_strip(authenticated_client):
    create_response = await authenticated_client.post(
        "/tasks",
        json={
            "title": "Estudar Python",
            "description": "Teste de atualização",
            "done": False,
        },
    )

    task_id = create_response.json()["id"]

    response = await authenticated_client.patch(
        f"/tasks/{task_id}",
        json={"title": "  Estudar FastAPI  "},
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Estudar FastAPI"


@pytest.mark.anyio
async def test_create_task_title_too_long(authenticated_client):
    response = await authenticated_client.post(
        "/tasks",
        json={
            "title": "A" * 201,
            "description": "Teste de tamanho",
            "done": False,
        },
    )

    assert response.status_code == 422


# =====================================================
# TESTES DE ISOLAMENTO ENTRE USUÁRIOS
# =====================================================


@pytest.mark.anyio
async def test_user_cannot_access_another_users_tasks(
    authenticated_client,
    user,
):
    # Primeiro usuário cria uma tarefa
    create_response = await authenticated_client.post(
        "/tasks",
        json={
            "title": "Tarefa privada",
            "description": "Pertence ao primeiro usuário",
            "done": False,
        },
    )

    assert create_response.status_code == 201

    task_id = create_response.json()["id"]

    # Cria um segundo usuário
    second_user_response = await authenticated_client.post(
        "/users",
        json={
            "name": "Segundo usuário",
            "email": "segundo@example.com",
            "password": "SenhaTeste123",
        },
    )

    assert second_user_response.status_code == 201

    second_user = second_user_response.json()

    # Segundo usuário realiza login
    login_response = await authenticated_client.post(
        "/auth/token",
        data={
            "username": second_user["email"],
            "password": "SenhaTeste123",
        },
    )

    assert login_response.status_code == 200

    second_token = login_response.json()["access_token"]

    # Substitui o token pelo do segundo usuário
    authenticated_client.headers.update({
        "Authorization": f"Bearer {second_token}"
    })

    response = await authenticated_client.get("/tasks")

    assert response.status_code == 200
    assert response.json() == []

    response = await authenticated_client.get(
        f"/tasks/{task_id}"
    )

    assert response.status_code == 404

    response = await authenticated_client.patch(
        f"/tasks/{task_id}",
        json={"done": True},
    )

    assert response.status_code == 404

    response = await authenticated_client.delete(
        f"/tasks/{task_id}"
    )

    assert response.status_code == 404


@pytest.mark.anyio
async def test_create_user(client):
    response = await client.post(
        "/users",
        json={
            "name": "João",
            "email": "joao@email.com",
            "password": "SenhaTeste123",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] is not None
    assert data["name"] == "João"
    assert data["email"] == "joao@email.com"


@pytest.mark.anyio
async def test_list_users(client):
    await client.post(
        "/users",
        json={
            "name": "Maria",
            "email": "maria@email.com",
            "password": "SenhaTeste123",
        },
    )

    response = await client.get("/users")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["name"] == "Maria"
    assert data[0]["email"] == "maria@email.com"


@pytest.mark.anyio
async def test_get_user(client):
    create_response = await client.post(
        "/users",
        json={
            "name": "Pedro",
            "email": "pedro@email.com",
            "password": "SenhaTeste123",
        },
    )

    user_id = create_response.json()["id"]

    response = await client.get(f"/users/{user_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == user_id
    assert data["name"] == "Pedro"
    assert data["email"] == "pedro@email.com"


@pytest.mark.anyio
async def test_get_user_not_found(client):
    response = await client.get("/users/999999")

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Usuário não encontrado"
    }


@pytest.mark.anyio
async def test_update_user(client):
    create_response = await client.post(
        "/users",
        json={
            "name": "João",
            "email": "joao@email.com",
            "password": "SenhaTeste123",
        },
    )

    user_id = create_response.json()["id"]

    response = await client.patch(
        f"/users/{user_id}",
        json={"name": "João Silva"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == user_id
    assert data["name"] == "João Silva"
    assert data["email"] == "joao@email.com"


@pytest.mark.anyio
async def test_update_user_not_found(client):
    response = await client.patch(
        "/users/999999",
        json={"name": "João Silva"},
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Usuário não encontrado"
    }


@pytest.mark.anyio
async def test_delete_user(client):
    create_response = await client.post(
        "/users",
        json={
            "name": "Carlos",
            "email": "carlos@email.com",
            "password": "SenhaTeste123",
        },
    )

    user_id = create_response.json()["id"]

    response = await client.delete(f"/users/{user_id}")

    assert response.status_code == 204

    get_response = await client.get(f"/users/{user_id}")

    assert get_response.status_code == 404


@pytest.mark.anyio
async def test_delete_user_not_found(client):
    response = await client.delete("/users/999999")

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Usuário não encontrado"
    }


# =====================================================
# TESTES DE VALIDAÇÃO DE USERS
# =====================================================

@pytest.mark.anyio
async def test_create_user_duplicate_email(client):
    await client.post(
        "/users",
        json={
            "name": "João",
            "email": "joao@email.com",
            "password": "SenhaTeste123",
        },
    )

    response = await client.post(
        "/users",
        json={
            "name": "Pedro",
            "email": "joao@email.com",
            "password": "SenhaTeste123",
        },
    )

    assert response.status_code == 409

    assert response.json() == {
        "detail": "Este e-mail já está cadastrado"
    }


@pytest.mark.anyio
async def test_create_user_invalid_email(client):
    response = await client.post(
        "/users",
        json={
            "name": "João",
            "email": "email-invalido",
            "password": "SenhaTeste123",
        },
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_user_name_only_spaces(client):
    response = await client.post(
        "/users",
        json={
            "name": "     ",
            "email": "joao@email.com",
            "password": "SenhaTeste123",
        },
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_user_name_too_long(client):
    response = await client.post(
        "/users",
        json={
            "name": "A" * 101,
            "email": "joao@email.com",
            "password": "SenhaTeste123",
        },
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_user_email_strip_and_lower(client):
    response = await client.post(
        "/users",
        json={
            "name": "João",
            "email": "  JOAO@EMAIL.COM  ",
            "password": "SenhaTeste123",
        },
    )

    assert response.status_code == 201

    assert response.json()["email"] == "joao@email.com"


@pytest.mark.anyio
async def test_update_user_empty_payload(client):
    create_response = await client.post(
        "/users",
        json={
            "name": "João",
            "email": "joao@email.com",
            "password": "SenhaTeste123",
        },
    )

    user_id = create_response.json()["id"]

    response = await client.patch(
        f"/users/{user_id}",
        json={},
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_update_user_email_null(client):
    create_response = await client.post(
        "/users",
        json={
            "name": "João",
            "email": "joao@email.com",
            "password": "SenhaTeste123",
        },
    )

    user_id = create_response.json()["id"]

    response = await client.patch(
        f"/users/{user_id}",
        json={"email": None},
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_update_user_duplicate_email(client):
    await client.post(
        "/users",
        json={
            "name": "João",
            "email": "joao@email.com",
            "password": "SenhaTeste123",
        },
    )

    second_response = await client.post(
        "/users",
        json={
            "name": "Maria",
            "email": "maria@email.com",
            "password": "SenhaTeste123",
        },
    )

    second_user_id = second_response.json()["id"]

    response = await client.patch(
        f"/users/{second_user_id}",
        json={"email": "joao@email.com"},
    )

    assert response.status_code == 409


@pytest.mark.anyio
async def test_create_user_password_is_hashed(client, test_session):
    password = "SenhaTeste123"

    response = await client.post(
        "/users",
        json={
            "name": "João",
            "email": "joao.hash@example.com",
            "password": password,
        },
    )

    assert response.status_code == 201

    result = await test_session.scalar(
        select(User).where(
            User.email == "joao.hash@example.com"
        )
    )

    assert result is not None
    assert result.password != password
    assert result.password.startswith("$argon2id$")
    assert verify_password(password, result.password)

    assert "password" not in response.json()


# =====================================================
# TESTES DE AUTENTICAÇÃO / LOGIN
# =====================================================


# =====================================================
# TESTES DE AUTENTICAÇÃO / LOGIN
# =====================================================

@pytest.mark.anyio
async def test_login_success(client, user):
    response = await client.post(
        "/auth/token",
        data={
            "username": user["email"],
            "password": "SenhaTeste123",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.anyio
async def test_login_user_not_found(client):
    response = await client.post(
        "/auth/token",
        data={
            "username": "inexistente@example.com",
            "password": "SenhaTeste123",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "E-mail ou senha incorretos"


@pytest.mark.anyio
async def test_login_wrong_password(client, user):
    response = await client.post(
        "/auth/token",
        data={
            "username": user["email"],
            "password": "SenhaErrada123",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "E-mail ou senha incorretos"


@pytest.mark.anyio
async def test_login_token_contains_user_id(client, user):
    response = await client.post(
        "/auth/token",
        data={
            "username": user["email"],
            "password": "SenhaTeste123",
        },
    )

    token = response.json()["access_token"]

    payload = jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.algorithm],
    )

    assert payload["sub"] == str(user["id"])
    assert "exp" in payload


# =====================================================
# TESTES DE PROTEÇÃO DAS ROTAS COM JWT
# =====================================================

@pytest.mark.parametrize(
    "method, url, payload",
    [
        ("POST", "/tasks", {
            "title": "Tarefa sem autenticação",
            "description": None,
            "done": False,
        }),
        ("GET", "/tasks", None),
        ("GET", "/tasks/1", None),
        ("PATCH", "/tasks/1", {"done": True}),
        ("DELETE", "/tasks/1", None),
    ],
)
@pytest.mark.anyio
async def test_tasks_without_token(client, method, url, payload):
    response = await client.request(
        method,
        url,
        json=payload,
    )

    assert response.status_code == 401


@pytest.mark.anyio
async def test_tasks_with_invalid_token(client):
    client.headers.update({
        "Authorization": "Bearer token_invalido"
    })

    response = await client.get("/tasks")

    assert response.status_code == 401


@pytest.mark.anyio
async def test_tasks_with_expired_token(client, user):
    expired_payload = {
        "sub": str(user["id"]),
        "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
    }

    expired_token = jwt.encode(
        expired_payload,
        settings.secret_key,
        algorithm=settings.algorithm,
    )

    client.headers.update({
        "Authorization": f"Bearer {expired_token}"
    })

    response = await client.get("/tasks")

    assert response.status_code == 401


@pytest.mark.anyio
async def test_tasks_with_token_of_deleted_user(
    client,
    user,
    test_session,
):
    login_response = await client.post(
        "/auth/token",
        data={
            "username": user["email"],
            "password": "SenhaTeste123",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    db_user = await test_session.get(User, user["id"])

    assert db_user is not None

    await test_session.delete(db_user)
    await test_session.commit()

    client.headers.update({
        "Authorization": f"Bearer {token}"
    })

    response = await client.get("/tasks")

    assert response.status_code == 401



@pytest.mark.anyio
async def test_refresh_token_success(
    client,
    user,
    test_session,
):
    from app.core.security import (
        create_refresh_token,
        hash_refresh_token,
    )
    from app.repositories import refresh_token_repository
    from datetime import datetime, timezone
    import jwt
    from app.database import settings

    old_refresh_token = create_refresh_token(
        data={"sub": str(user["id"])}
    )

    payload = jwt.decode(
        old_refresh_token,
        settings.secret_key,
        algorithms=[settings.algorithm],
    )

    expires_at = datetime.fromtimestamp(
        payload["exp"],
        tz=timezone.utc,
    )

    old_record = await refresh_token_repository.create_refresh_token(
        session=test_session,
        user_id=user["id"],
        token_hash=hash_refresh_token(old_refresh_token),
        expires_at=expires_at,
    )

    await test_session.commit()

    response = await client.post(
        "/auth/refresh",
        json={"refresh_token": old_refresh_token},
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

    assert old_record.revoked is True

    new_hash = hash_refresh_token(data["refresh_token"])

    new_record = await refresh_token_repository.get_refresh_token_by_hash(
        test_session,
        new_hash,
    )

    assert new_record is not None
    assert new_record.revoked is False



@pytest.mark.anyio
async def test_refresh_token_reuse_rejected(client, user, test_session):
    from app.core.security import create_refresh_token, hash_refresh_token
    from app.repositories import refresh_token_repository
    from datetime import datetime, timezone
    import jwt
    from app.database import settings

    old_refresh_token = create_refresh_token(
        data={"sub": str(user["id"])}
    )

    payload = jwt.decode(
        old_refresh_token,
        settings.secret_key,
        algorithms=[settings.algorithm],
    )

    expires_at = datetime.fromtimestamp(
        payload["exp"],
        tz=timezone.utc,
    )

    await refresh_token_repository.create_refresh_token(
        session=test_session,
        user_id=user["id"],
        token_hash=hash_refresh_token(old_refresh_token),
        expires_at=expires_at,
    )

    await test_session.commit()

    # Primeira utilização: deve funcionar.
    first_response = await client.post(
        "/auth/refresh",
        json={"refresh_token": old_refresh_token},
    )

    assert first_response.status_code == 200

    # Segunda utilização do mesmo token: deve ser rejeitada.
    second_response = await client.post(
        "/auth/refresh",
        json={"refresh_token": old_refresh_token},
    )

    assert second_response.status_code == 401



@pytest.mark.anyio
async def test_logout_success(client, user, test_session):
    from app.core.security import create_refresh_token, hash_refresh_token
    from app.repositories import refresh_token_repository
    from datetime import datetime, timezone
    import jwt
    from app.database import settings

    refresh_token = create_refresh_token(
        data={"sub": str(user["id"])}
    )

    payload = jwt.decode(
        refresh_token,
        settings.secret_key,
        algorithms=[settings.algorithm],
    )

    expires_at = datetime.fromtimestamp(
        payload["exp"],
        tz=timezone.utc,
    )

    stored_token = await refresh_token_repository.create_refresh_token(
        session=test_session,
        user_id=user["id"],
        token_hash=hash_refresh_token(refresh_token),
        expires_at=expires_at,
    )

    await test_session.commit()

    response = await client.post(
        "/auth/logout",
        json={"refresh_token": refresh_token},
    )

    assert response.status_code == 204
    assert stored_token.revoked is True



@pytest.mark.anyio
async def test_refresh_token_after_logout_rejected(
    client,
    user,
    test_session,
):
    refresh_token = create_refresh_token(
        data={"sub": str(user["id"])}
    )

    payload = jwt.decode(
        refresh_token,
        settings.secret_key,
        algorithms=[settings.algorithm],
    )

    expires_at = datetime.fromtimestamp(
        payload["exp"],
        tz=timezone.utc,
    )

    await refresh_token_repository.create_refresh_token(
        session=test_session,
        user_id=user["id"],
        token_hash=hash_refresh_token(refresh_token),
        expires_at=expires_at,
    )

    await test_session.commit()

    # Executa o logout.
    logout_response = await client.post(
        "/auth/logout",
        json={"refresh_token": refresh_token},
    )

    assert logout_response.status_code == 204

    # Tenta renovar usando o token revogado.
    refresh_response = await client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert refresh_response.status_code == 401


@pytest.mark.anyio
async def test_refresh_token_concurrent_requests(
    concurrent_client,
    concurrent_session_factory,
):
    # 1. Criar um usuário diretamente no banco de testes
    email = f"concorrencia_{uuid.uuid4().hex}@example.com"

    async with concurrent_session_factory() as session:
        test_user = User(
            name="Usuário de concorrência",
            email=email,
            password="senha_hash_de_teste",
        )

        session.add(test_user)
        await session.flush()

        user_id = test_user.id

        # 2. Criar um refresh token para esse usuário
        refresh_token = create_refresh_token(
            data={"sub": str(user_id)}
        )

        payload = jwt.decode(
            refresh_token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )

        expires_at = datetime.fromtimestamp(
            payload["exp"],
            tz=timezone.utc,
        )

        await refresh_token_repository.create_refresh_token(
            session=session,
            user_id=user_id,
            token_hash=hash_refresh_token(refresh_token),
            expires_at=expires_at,
        )

        await session.commit()

    # 3. Enviar duas requisições simultâneas com o mesmo token
    results = await asyncio.gather(
        concurrent_client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token},
        ),
        concurrent_client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token},
        ),
    )

    # 4. Apenas uma requisição deve conseguir renovar o token
    status_codes = sorted(
        response.status_code for response in results
    )

    assert status_codes == [200, 401]



@pytest.mark.anyio
async def test_solicitar_soma(client, monkeypatch):
    chamada = {}

    def fake_delay(a, b):
        chamada["a"] = a
        chamada["b"] = b
        return SimpleNamespace(id="celery-task-123")

    monkeypatch.setattr(celery_tasks.somar, "delay", fake_delay)

    response = await client.post(
        "/background-tasks/somar",
        json={"a": 10, "b": 20},
    )

    assert response.status_code == 200
    assert response.json() == {
        "task_id": "celery-task-123",
        "status": "PENDING",
    }

    assert chamada == {"a": 10, "b": 20}


@pytest.mark.anyio
async def test_consultar_tarefa_sucesso(client, monkeypatch):
    tarefa_simulada = SimpleNamespace(
        successful=lambda: True,
        failed=lambda: False,
        result=30,
        status="SUCCESS",
    )

    monkeypatch.setattr(
        celery_tasks.celery_app,
        "AsyncResult",
        lambda task_id: tarefa_simulada,
    )

    response = await client.get(
        "/background-tasks/celery-task-123"
    )

    assert response.status_code == 200
    assert response.json() == {
        "task_id": "celery-task-123",
        "status": "SUCCESS",
        "result": 30,
        "error": None,
    }


@pytest.mark.anyio
async def test_consultar_tarefa_pendente(client, monkeypatch):
    tarefa_simulada = SimpleNamespace(
        successful=lambda: False,
        failed=lambda: False,
        result=None,
        status="PENDING",
    )

    monkeypatch.setattr(
        celery_tasks.celery_app,
        "AsyncResult",
        lambda task_id: tarefa_simulada,
    )

    response = await client.get(
        "/background-tasks/celery-task-123"
    )

    assert response.status_code == 200
    assert response.json() == {
        "task_id": "celery-task-123",
        "status": "PENDING",
        "result": None,
        "error": None,
    }


@pytest.mark.anyio
async def test_consultar_tarefa_falha(client, monkeypatch):
    tarefa_simulada = SimpleNamespace(
        successful=lambda: False,
        failed=lambda: True,
        result=RuntimeError("Erro simulado"),
        status="FAILURE",
    )

    monkeypatch.setattr(
        celery_tasks.celery_app,
        "AsyncResult",
        lambda task_id: tarefa_simulada,
    )

    response = await client.get(
        "/background-tasks/celery-task-123"
    )

    assert response.status_code == 200
    assert response.json() == {
        "task_id": "celery-task-123",
        "status": "FAILURE",
        "result": None,
        "error": "Erro simulado",
    }



@pytest.mark.anyio
async def test_solicitar_soma_rejeita_texto(client):
    response = await client.post(
        "/background-tasks/somar",
        json={"a": "dez", "b": 20},
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_solicitar_soma_rejeita_decimal(client):
    response = await client.post(
        "/background-tasks/somar",
        json={"a": 10.5, "b": 20},
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_solicitar_soma_rejeita_campo_ausente(client):
    response = await client.post(
        "/background-tasks/somar",
        json={"a": 10},
    )

    assert response.status_code == 422



@pytest.mark.anyio
async def test_consultar_tarefa_em_execucao(client, monkeypatch):
    tarefa_simulada = SimpleNamespace(
        status="STARTED",
        result=None,
    )

    monkeypatch.setattr(
        celery_tasks.celery_app,
        "AsyncResult",
        lambda task_id: tarefa_simulada,
    )

    response = await client.get(
        "/background-tasks/celery-task-123"
    )

    assert response.status_code == 200
    assert response.json() == {
        "task_id": "celery-task-123",
        "status": "STARTED",
        "result": None,
        "error": None,
    }



@pytest.mark.anyio
async def test_consultar_tarefa_em_nova_tentativa(client, monkeypatch):
    tarefa_simulada = SimpleNamespace(
        status="RETRY",
        result=None,
    )

    monkeypatch.setattr(
        celery_tasks.celery_app,
        "AsyncResult",
        lambda task_id: tarefa_simulada,
    )

    response = await client.get(
        "/background-tasks/celery-task-123"
    )

    assert response.status_code == 200
    assert response.json() == {
        "task_id": "celery-task-123",
        "status": "RETRY",
        "result": None,
        "error": None,
    }


@pytest.mark.anyio
async def test_consultar_tarefa_revogada(client, monkeypatch):
    tarefa_simulada = SimpleNamespace(
        status="REVOKED",
        result=None,
    )

    monkeypatch.setattr(
        celery_tasks.celery_app,
        "AsyncResult",
        lambda task_id: tarefa_simulada,
    )

    response = await client.get(
        "/background-tasks/celery-task-123"
    )

    assert response.status_code == 200
    assert response.json() == {
        "task_id": "celery-task-123",
        "status": "REVOKED",
        "result": None,
        "error": None,
    }
