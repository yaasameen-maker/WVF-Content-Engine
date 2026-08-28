"""add scheduled_date to content_items

Revision ID: d8f1a4c6e9b2
Revises: a7c3e9f1b2d4
Create Date: 2026-08-27 00:00:00.000000

Nullable, staff-set target publish date shown on /calendar — separate
from the parent event's date since a post isn't always published the
same day its event happens. Purely organizational: does not queue or
auto-publish anything (posting stays a manual "Post to X" click).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd8f1a4c6e9b2'
down_revision: Union[str, None] = 'a7c3e9f1b2d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('content_items', sa.Column('scheduled_date', sa.Date(), nullable=True))
    op.create_index(
        op.f('ix_content_items_scheduled_date'), 'content_items', ['scheduled_date'], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_content_items_scheduled_date'), table_name='content_items')
    op.drop_column('content_items', 'scheduled_date')
