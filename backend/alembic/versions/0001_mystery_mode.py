"""Add is_mystery and revealed_to fields to messages table.

Revision ID: 0001_mystery_mode
Revises: 
Create Date: 2026-03-25
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, UUID

# revision identifiers
revision = "0001_mystery_mode"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "messages",
        sa.Column(
            "is_mystery",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
    )
    op.add_column(
        "messages",
        sa.Column(
            "revealed_to",
            ARRAY(UUID(as_uuid=True)),
            nullable=False,
            server_default="{}",
        ),
    )


def downgrade() -> None:
    op.drop_column("messages", "revealed_to")
    op.drop_column("messages", "is_mystery")
