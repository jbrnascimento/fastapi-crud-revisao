
import asyncio

from logging.config import fileConfig

from alembic import context

from app.database import engine
from app.models import Base, Task, User, RefreshToken


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = str(engine.url)

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        version_table_schema="fastapi_crud",
        compare_type=True,
        include_name=include_name,
    )

    with context.begin_transaction():
        context.run_migrations()


def include_name(name, type_, parent_names):
    if type_ == "schema":
        return name in (None, "fastapi_crud")

    if type_ == "table":
        return name != "alembic_version"

    return True


def do_run_migrations(connection):
    # Garante que o schema exista antes de o Alembic criar
    # sua tabela de controle (alembic_version).
    with connection.begin():
        connection.exec_driver_sql(
            "CREATE SCHEMA IF NOT EXISTS fastapi_crud"
        )
        
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_schemas=True,
        version_table_schema="fastapi_crud",
        compare_type=True,
        include_name=include_name,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_async_migrations())
