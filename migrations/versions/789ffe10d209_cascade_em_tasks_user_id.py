"""cascade em tasks.user_id

Revision ID: 789ffe10d209
Revises: fd5d6b810c5c
Create Date: 2026-11-09 18:15:37.215067

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '789ffe10d209'
down_revision: Union[str, Sequence[str], None] = 'fd5d6b810c5c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint(
        op.f("fk_tasks_user_id_users"),
        "tasks",
        schema="fastapi_crud",
        type_="foreignkey",
    )
    op.create_foreign_key(
        op.f("fk_tasks_user_id_users"),
        "tasks",
        "users",
        ["user_id"],
        ["id"],
        source_schema="fastapi_crud",
        referent_schema="fastapi_crud",
        onupdate="CASCADE",
        ondelete="CASCADE",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        op.f("fk_tasks_user_id_users"),
        "tasks",
        schema="fastapi_crud",
        type_="foreignkey",
    )
    op.create_foreign_key(
        op.f("fk_tasks_user_id_users"),
        "tasks",
        "users",
        ["user_id"],
        ["id"],
        source_schema="fastapi_crud",
        referent_schema="fastapi_crud",
    )