"""Add performance indexes for geospatial queries, messages, and reactions.

Revision ID: 0002_performance_indexes
Revises: 0001_mystery_mode
Create Date: 2026-03-25
"""
from alembic import op

# revision identifiers
revision = "0002_performance_indexes"
down_revision = "0001_mystery_mode"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── PostGIS GIST index for fast radius searches ──────────────────────────
    # Accelerates ST_DWithin / ST_Distance queries on users.location
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_users_location_gist "
        "ON users USING GIST (location)"
    )

    # ── Index to quickly find recently active users ──────────────────────────
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_users_last_active "
        "ON users (location_updated_at) "
        "WHERE location_updated_at IS NOT NULL"
    )

    # ── Messages: ordering and recipient look-ups ────────────────────────────
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_messages_created_at "
        "ON messages (created_at DESC)"
    )

    # PostGIS GIST index on message locations for nearby-message queries
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_messages_location_gist "
        "ON messages USING GIST (location)"
    )

    # ── Reactions: look-up by message ────────────────────────────────────────
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_reactions_message "
        "ON reactions (message_id)"
    )

    # ── Reactions: look-up by user ────────────────────────────────────────────
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_reactions_user "
        "ON reactions (user_id)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_reactions_user")
    op.execute("DROP INDEX IF EXISTS idx_reactions_message")
    op.execute("DROP INDEX IF EXISTS idx_messages_location_gist")
    op.execute("DROP INDEX IF EXISTS idx_messages_created_at")
    op.execute("DROP INDEX IF EXISTS idx_users_last_active")
    op.execute("DROP INDEX IF EXISTS idx_users_location_gist")
