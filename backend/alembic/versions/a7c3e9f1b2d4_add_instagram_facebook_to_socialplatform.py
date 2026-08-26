"""add instagram and facebook to socialplatform enum

Revision ID: a7c3e9f1b2d4
Revises: c8e2f5a1d9b7
Create Date: 2026-08-26 00:00:00.000000

Scaffolds the DB side of Instagram/Facebook "Connect" buttons (Meta Graph
API, one app covers both) — see app/services/meta_client.py. Posting won't
actually work until WVF's Meta Developer app passes App Review; this
migration only makes the enum values valid to store.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a7c3e9f1b2d4'
down_revision: Union[str, None] = 'c8e2f5a1d9b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ALTER TYPE ... ADD VALUE cannot run inside the same transaction as
    # other schema changes on some PG versions — this migration only does
    # this, so autocommit_block() keeps it safe regardless.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE socialplatform ADD VALUE IF NOT EXISTS 'instagram'")
        op.execute("ALTER TYPE socialplatform ADD VALUE IF NOT EXISTS 'facebook'")


def downgrade() -> None:
    # Postgres has no ALTER TYPE ... DROP VALUE — removing an enum value
    # requires rebuilding the type (rename old, create new, migrate
    # dependent columns, drop old). Not worth the destructive complexity
    # for a downgrade path; document instead of half-implementing it.
    raise NotImplementedError(
        "Cannot drop enum values in Postgres without rebuilding the "
        "socialplatform type. If you need to fully revert this, do it "
        "manually: rename the type, recreate it without 'instagram'/"
        "'facebook', migrate social_connections/social_posts/"
        "oauth_pkce_states.platform to the new type, drop the old one."
    )
