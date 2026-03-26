"""Add performance indexes: GIST for message locations and B-tree for created_at / user_id.

Revision ID: 0003_add_indexes
Revises: 0002_premium_tiers
Create Date: 2026-03-25
"""
from alembic import op

# revision identifiers
revision = "0003_add_indexes"
down_revision = "0002_premium_tiers"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # GIST index for PostGIS spatial queries — dramatically speeds up ST_DWithin
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_messages_location_gist "
        "ON messages USING GIST (location);"
    )
    # B-tree index for time-ordered message pagination
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_messages_created_at "
        "ON messages (created_at DESC);"
    )
    # B-tree index for per-user message lookups
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_messages_user_id "
        "ON messages (user_id);"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_messages_user_id;")
    op.execute("DROP INDEX IF EXISTS idx_messages_created_at;")
    op.execute("DROP INDEX IF EXISTS idx_messages_location_gist;")
