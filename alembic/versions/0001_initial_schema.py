"""initial_schema

Revision ID: 0001
Revises:
Create Date: 2026-08-16

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "clients",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_client_is_active", "clients", ["is_active"])

    op.create_table(
        "instances",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("client_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="disconnected"),
        sa.Column("provider_instance_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider_instance_id"),
    )
    op.create_index("ix_instance_client_id", "instances", ["client_id"])
    op.create_index("ix_instance_status", "instances", ["status"])

    op.create_table(
        "messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("instance_id", sa.Uuid(), nullable=False),
        sa.Column("direction", sa.String(10), nullable=False),
        sa.Column("content_type", sa.String(20), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("remote_jid", sa.String(255), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("provider_message_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["instance_id"], ["instances.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_message_instance_id", "messages", ["instance_id"])
    op.create_index("ix_message_created_at", "messages", ["created_at"])
    op.create_index("ix_message_provider_message_id", "messages", ["provider_message_id"])

    op.create_table(
        "webhook_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("instance_id", sa.Uuid(), nullable=True),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("raw_payload", JSONB(), nullable=False),
        sa.Column("processing_status", sa.String(20), nullable=False, server_default="received"),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["instance_id"], ["instances.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_webhook_event_instance_id", "webhook_events", ["instance_id"])
    op.create_index("ix_webhook_event_event_type", "webhook_events", ["event_type"])
    op.create_index("ix_webhook_event_created_at", "webhook_events", ["created_at"])

    op.create_table(
        "error_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("context", sa.String(255), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("details", JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_error_log_context", "error_logs", ["context"])
    op.create_index("ix_error_log_created_at", "error_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_error_log_created_at", table_name="error_logs")
    op.drop_index("ix_error_log_context", table_name="error_logs")
    op.drop_table("error_logs")

    op.drop_index("ix_webhook_event_created_at", table_name="webhook_events")
    op.drop_index("ix_webhook_event_event_type", table_name="webhook_events")
    op.drop_index("ix_webhook_event_instance_id", table_name="webhook_events")
    op.drop_table("webhook_events")

    op.drop_index("ix_message_provider_message_id", table_name="messages")
    op.drop_index("ix_message_created_at", table_name="messages")
    op.drop_index("ix_message_instance_id", table_name="messages")
    op.drop_table("messages")

    op.drop_index("ix_instance_status", table_name="instances")
    op.drop_index("ix_instance_client_id", table_name="instances")
    op.drop_table("instances")

    op.drop_index("ix_client_is_active", table_name="clients")
    op.drop_table("clients")
