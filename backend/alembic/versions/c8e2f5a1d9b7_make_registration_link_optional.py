"""make registration_link optional

Revision ID: c8e2f5a1d9b7
Revises: b6f1d4a8c3e5
Create Date: 2026-08-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8e2f5a1d9b7'
down_revision: Union[str, None] = 'b6f1d4a8c3e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('events', 'registration_link', existing_type=sa.String(length=500), nullable=True)


def downgrade() -> None:
    # Any existing NULL rows would violate the NOT NULL constraint on
    # downgrade — backfill a placeholder first so this is reversible.
    op.execute("UPDATE events SET registration_link = '' WHERE registration_link IS NULL")
    op.alter_column('events', 'registration_link', existing_type=sa.String(length=500), nullable=False)
