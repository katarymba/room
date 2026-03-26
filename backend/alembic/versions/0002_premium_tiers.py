"""Add premium tier fields to users table.

Revision ID: 0002_premium_tiers
Revises: 0001_mystery_mode
Create Date: 2026-03-25
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "0002_premium_tiers"
down_revision = "0001_mystery_mode"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("tier", sa.String(20), nullable=False, server_default="free"),
    )
    op.add_column(
        "users",
        sa.Column("subscription_expires_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("daily_message_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "users",
        sa.Column("last_message_reset", sa.DateTime(), nullable=False, server_default="now()"),
    )


def downgrade() -> None:
    op.drop_column("users", "last_message_reset")
    op.drop_column("users", "daily_message_count")
    op.drop_column("users", "subscription_expires_at")
    op.drop_column("users", "tier")
