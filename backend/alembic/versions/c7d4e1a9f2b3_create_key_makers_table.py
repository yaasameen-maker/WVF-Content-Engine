"""create key_makers table

Revision ID: c7d4e1a9f2b3
Revises: a1f3c9d2e6b4
Create Date: 2026-08-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7d4e1a9f2b3'
down_revision: Union[str, None] = 'a1f3c9d2e6b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'key_makers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('business_name', sa.String(length=255), nullable=False),
        sa.Column('owner_name', sa.String(length=255), nullable=False),
        sa.Column('business_type', sa.String(length=255), nullable=True),
        sa.Column('website', sa.String(length=500), nullable=True),
        sa.Column('social_media', sa.Text(), nullable=True),
        sa.Column('testimonial_quote', sa.Text(), nullable=True),
        sa.Column('video_link', sa.String(length=500), nullable=True),
        sa.Column('photo_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_key_makers_id'), 'key_makers', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_key_makers_id'), table_name='key_makers')
    op.drop_table('key_makers')
