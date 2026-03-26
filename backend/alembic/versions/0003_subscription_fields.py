"""Add subscription tier and freemium tracking fields to the users table.

Revision ID: 0003_subscription_fields
Revises: 0002_performance_indexes
Create Date: 2026-03-25
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "0003_subscription_fields"
down_revision = "0002_performance_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "subscription_tier",
            sa.String(20),
            nullable=False,
            server_default="free",
        ),
    )
    op.add_column(
        "users",
        sa.Column("subscription_expires_at", sa.DateTime, nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "daily_message_count",
            sa.Integer,
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "users",
        sa.Column("last_message_reset_date", sa.Date, nullable=True),
    )

    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_users_subscription "
        "ON users (subscription_tier)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_users_subscription")
    op.drop_column("users", "last_message_reset_date")
    op.drop_column("users", "daily_message_count")
    op.drop_column("users", "subscription_expires_at")
    op.drop_column("users", "subscription_tier")
