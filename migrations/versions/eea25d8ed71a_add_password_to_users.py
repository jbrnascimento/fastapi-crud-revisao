"""add password to users

Revision ID: eea25d8ed71a
Revises: 789ffe10d209
Create Date: 2026-11-14 16:57:49.156317

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eea25d8ed71a'
down_revision: Union[str, Sequence[str], None] = '789ffe10d209'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column(
            'password',
            sa.String(length=255),
            nullable=False
        ),
        schema='fastapi_crud'
    )


def downgrade() -> None:
    op.drop_column(
        'users',
        'password',
        schema='fastapi_crud'
    )