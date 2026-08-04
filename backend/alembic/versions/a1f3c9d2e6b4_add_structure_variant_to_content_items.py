"""add structure_variant to content_items

Revision ID: a1f3c9d2e6b4
Revises: 7362ece56f7b
Create Date: 2026-08-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1f3c9d2e6b4'
down_revision: Union[str, None] = '7362ece56f7b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'content_items',
        sa.Column('structure_variant', sa.String(length=50), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('content_items', 'structure_variant')
