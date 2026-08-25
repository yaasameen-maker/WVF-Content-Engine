"""add key maker bio fields

Revision ID: b6f1d4a8c3e5
Revises: f4a9c2d7e8b1
Create Date: 2026-08-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b6f1d4a8c3e5'
down_revision: Union[str, None] = 'f4a9c2d7e8b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('key_makers', sa.Column('title', sa.String(length=255), nullable=True))
    op.add_column('key_makers', sa.Column('location', sa.String(length=255), nullable=True))
    op.add_column('key_makers', sa.Column('industry', sa.String(length=255), nullable=True))
    op.add_column('key_makers', sa.Column('key_quotes', sa.Text(), nullable=True))
    op.add_column('key_makers', sa.Column('story', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('key_makers', 'story')
    op.drop_column('key_makers', 'key_quotes')
    op.drop_column('key_makers', 'industry')
    op.drop_column('key_makers', 'location')
    op.drop_column('key_makers', 'title')
