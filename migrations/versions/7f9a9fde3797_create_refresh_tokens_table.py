"""create refresh tokens table

Revision ID: 7f9a9fde3797
Revises: eea25d8ed71a
Create Date: 2026-11-17 18:17:39.719163

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f9a9fde3797'
down_revision: Union[str, Sequence[str], None] = 'eea25d8ed71a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["fastapi_crud.users.id"],
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
        schema="fastapi_crud",
    )

    op.create_index(
        "ix_fastapi_crud_refresh_tokens_user_id",
        "refresh_tokens",
        ["user_id"],
        unique=False,
        schema="fastapi_crud",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_fastapi_crud_refresh_tokens_user_id",
        table_name="refresh_tokens",
        schema="fastapi_crud",
    )

    op.drop_table(
        "refresh_tokens",
        schema="fastapi_crud",
    )
