"""create content_composed_images table

Revision ID: c1a6f8b3d5e7
Revises: b2e7f4a9c1d6
Create Date: 2026-09-13 00:00:00.000000

Composed (photo + text overlay) images for the New Campaign flow — see
app/models/media.py's ComposedImage docstring. Proposed scope addition,
not yet approved by WVF, and a step beyond PROJECT_CONTEXT.md's "no
image files generated or stored" line. Fully reversible: a brand-new
table with no data dependency from any existing row.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1a6f8b3d5e7'
down_revision: Union[str, None] = 'b2e7f4a9c1d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'content_composed_images',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('content_item_id', sa.Integer(), nullable=False),
        sa.Column('source_photo_id', sa.Integer(), nullable=True),
        sa.Column('object_key', sa.String(length=500), nullable=False),
        sa.Column('public_url', sa.String(length=500), nullable=False),
        sa.Column('content_type', sa.String(length=100), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['content_item_id'], ['content_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_photo_id'], ['photo_assets.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('object_key'),
    )
    op.create_index(op.f('ix_content_composed_images_id'), 'content_composed_images', ['id'], unique=False)
    op.create_index(
        op.f('ix_content_composed_images_content_item_id'),
        'content_composed_images',
        ['content_item_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_content_composed_images_source_photo_id'),
        'content_composed_images',
        ['source_photo_id'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_content_composed_images_source_photo_id'), table_name='content_composed_images')
    op.drop_index(op.f('ix_content_composed_images_content_item_id'), table_name='content_composed_images')
    op.drop_index(op.f('ix_content_composed_images_id'), table_name='content_composed_images')
    op.drop_table('content_composed_images')
