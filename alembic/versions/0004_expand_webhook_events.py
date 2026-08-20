"""expand_webhook_events

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-19

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("webhook_events", sa.Column("client_id", sa.Uuid(), nullable=True))
    op.add_column("webhook_events", sa.Column("provider", sa.String(50), nullable=True))
    op.add_column("webhook_events", sa.Column("provider_instance_name", sa.String(255), nullable=True))
    op.add_column("webhook_events", sa.Column("normalized_payload", JSONB(), nullable=True))
    op.add_column("webhook_events", sa.Column("forwarded_to_n8n", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("webhook_events", sa.Column("n8n_status_code", sa.Integer(), nullable=True))
    op.add_column("webhook_events", sa.Column("n8n_response", JSONB(), nullable=True))
    op.add_column("webhook_events", sa.Column("received_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("webhook_events", sa.Column("forwarded_at", sa.DateTime(timezone=True), nullable=True))

    op.create_foreign_key(
        "fk_webhook_events_client_id",
        "webhook_events",
        "clients",
        ["client_id"],
        ["id"],
    )

    op.create_index("ix_webhook_event_client_id", "webhook_events", ["client_id"])
    op.create_index("ix_webhook_event_provider_instance_name", "webhook_events", ["provider_instance_name"])
    op.create_index("ix_webhook_event_forwarded_to_n8n", "webhook_events", ["forwarded_to_n8n"])
    op.create_index("ix_webhook_event_received_at", "webhook_events", ["received_at"])


def downgrade() -> None:
    op.drop_index("ix_webhook_event_received_at", table_name="webhook_events")
    op.drop_index("ix_webhook_event_forwarded_to_n8n", table_name="webhook_events")
    op.drop_index("ix_webhook_event_provider_instance_name", table_name="webhook_events")
    op.drop_index("ix_webhook_event_client_id", table_name="webhook_events")
    op.drop_constraint("fk_webhook_events_client_id", "webhook_events", type_="foreignkey")
    op.drop_column("webhook_events", "forwarded_at")
    op.drop_column("webhook_events", "received_at")
    op.drop_column("webhook_events", "n8n_response")
    op.drop_column("webhook_events", "n8n_status_code")
    op.drop_column("webhook_events", "forwarded_to_n8n")
    op.drop_column("webhook_events", "normalized_payload")
    op.drop_column("webhook_events", "provider_instance_name")
    op.drop_column("webhook_events", "provider")
    op.drop_column("webhook_events", "client_id")
