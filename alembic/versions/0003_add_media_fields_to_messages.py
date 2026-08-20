"""add_media_fields_to_messages

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-18

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("messages", sa.Column("media_url", sa.Text(), nullable=True))
    op.add_column("messages", sa.Column("filename", sa.String(255), nullable=True))
    op.add_column("messages", sa.Column("raw_payload", JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("messages", "raw_payload")
    op.drop_column("messages", "filename")
    op.drop_column("messages", "media_url")
