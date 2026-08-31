"""add scheduled_time to content_items

Revision ID: e1c7a3f9d2b5
Revises: d8f1a4c6e9b2
Create Date: 2026-08-31 00:00:00.000000

Optional free-text time-of-day reminder alongside scheduled_date (e.g.
"2:30 PM") — display-only, not combined into a real datetime and not
read by any automation. Posting stays a manual "Post to X" click.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1c7a3f9d2b5'
down_revision: Union[str, None] = 'd8f1a4c6e9b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('content_items', sa.Column('scheduled_time', sa.String(length=20), nullable=True))


def downgrade() -> None:
    op.drop_column('content_items', 'scheduled_time')
