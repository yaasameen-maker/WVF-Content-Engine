"""create photo_assets table

Revision ID: b2e7f4a9c1d6
Revises: a4d9c6e2b8f1
Create Date: 2026-09-09 00:00:00.000000

Staff photo library (see app/models/media.py's module docstring) —
proposed scope addition, not yet approved by WVF. Fully reversible: a
brand-new table with no data dependency from any existing row, unlike
the enum-value-addition migrations elsewhere in this project.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2e7f4a9c1d6'
down_revision: Union[str, None] = 'a4d9c6e2b8f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'photo_assets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('object_key', sa.String(length=500), nullable=False),
        sa.Column('public_url', sa.String(length=500), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('content_type', sa.String(length=100), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column('key_maker_id', sa.Integer(), nullable=True),
        sa.Column('event_id', sa.Integer(), nullable=True),
        sa.Column('caption', sa.Text(), nullable=True),
        sa.Column('uploaded_by', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['key_maker_id'], ['key_makers.id']),
        sa.ForeignKeyConstraint(['event_id'], ['events.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('object_key'),
    )
    op.create_index(op.f('ix_photo_assets_id'), 'photo_assets', ['id'], unique=False)
    op.create_index(op.f('ix_photo_assets_key_maker_id'), 'photo_assets', ['key_maker_id'], unique=False)
    op.create_index(op.f('ix_photo_assets_event_id'), 'photo_assets', ['event_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_photo_assets_event_id'), table_name='photo_assets')
    op.drop_index(op.f('ix_photo_assets_key_maker_id'), table_name='photo_assets')
    op.drop_index(op.f('ix_photo_assets_id'), table_name='photo_assets')
    op.drop_table('photo_assets')
