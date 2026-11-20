"""test schema detection

Revision ID: fd5d6b810c5c
Revises: 26a4fb6118ce
Create Date: 2026-11-06 13:18:27.630405

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fd5d6b810c5c'
down_revision: Union[str, Sequence[str], None] = '26a4fb6118ce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=150), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        schema='fastapi_crud'
    )

    op.add_column(
        'tasks',
        sa.Column('user_id', sa.Integer(), nullable=False),
        schema='fastapi_crud'
    )

    op.create_foreign_key(
        'fk_tasks_user_id_users',
        'tasks',
        'users',
        ['user_id'],
        ['id'],
        source_schema='fastapi_crud',
        referent_schema='fastapi_crud'
    )


def downgrade() -> None:
    op.drop_constraint(
        'fk_tasks_user_id_users',
        'tasks',
        schema='fastapi_crud',
        type_='foreignkey'
    )

    op.drop_column(
        'tasks',
        'user_id',
        schema='fastapi_crud'
    )

    op.drop_table(
        'users',
        schema='fastapi_crud'
    )