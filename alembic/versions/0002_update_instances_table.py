"""update_instances_table

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-18

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add api_key_hash to clients
    op.add_column(
        "clients",
        sa.Column("api_key_hash", sa.String(255), nullable=True, unique=True),
    )

    # Rename 'name' to 'display_name'
    op.alter_column("instances", "name", new_column_name="display_name")

    # Update status default and valid values (string enum, no native enum)
    op.alter_column(
        "instances",
        "status",
        existing_type=sa.String(20),
        server_default="created",
    )

    # Add new columns
    op.add_column("instances", sa.Column("provider", sa.String(50), nullable=True))
    op.add_column("instances", sa.Column("phone_number", sa.String(20), nullable=True))
    op.add_column("instances", sa.Column("n8n_webhook_url", sa.Text(), nullable=True))
    op.add_column(
        "instances",
        sa.Column("webhook_enabled", sa.Boolean(), nullable=True, server_default="true"),
    )

    # Backfill provider for existing rows
    op.execute("UPDATE instances SET provider = 'evolution' WHERE provider IS NULL")

    # Now make provider NOT NULL
    op.alter_column("instances", "provider", nullable=False)

    # Make webhook_enabled NOT NULL
    op.alter_column("instances", "webhook_enabled", nullable=False)


def downgrade() -> None:
    op.drop_column("clients", "api_key_hash")

    op.drop_column("instances", "webhook_enabled")
    op.drop_column("instances", "n8n_webhook_url")
    op.drop_column("instances", "phone_number")
    op.drop_column("instances", "provider")

    op.alter_column(
        "instances",
        "status",
        existing_type=sa.String(20),
        server_default="disconnected",
    )

    op.alter_column("instances", "display_name", new_column_name="name")
