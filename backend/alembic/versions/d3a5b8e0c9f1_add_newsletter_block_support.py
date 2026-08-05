"""add newsletter_block support to content_items

Revision ID: d3a5b8e0c9f1
Revises: e2b8f6c1a4d7
Create Date: 2026-08-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd3a5b8e0c9f1'
down_revision: Union[str, None] = 'e2b8f6c1a4d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Relax event_id: some newsletter_block rows (boilerplate, grant_flyer,
    # member_spotlight) are reused across issues, not tied to one event.
    op.alter_column('content_items', 'event_id', existing_type=sa.Integer(), nullable=True)

    op.add_column(
        'content_items',
        sa.Column('key_maker_id', sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        'fk_content_items_key_maker_id',
        'content_items', 'key_makers',
        ['key_maker_id'], ['id'],
    )
    op.create_index(
        op.f('ix_content_items_key_maker_id'), 'content_items', ['key_maker_id'], unique=False
    )

    # Extend the content_type enum with the new value.
    op.execute("ALTER TYPE contenttype ADD VALUE IF NOT EXISTS 'NEWSLETTER_BLOCK'")

    # New enum for which of the 6 modular newsletter sections a row is.
    newsletter_block_type = sa.Enum(
        'FEATURE_ARTICLE', 'EVENTS_LIST', 'GRANT_FLYER',
        'TIPS_CTA', 'MEMBER_SPOTLIGHT', 'BOILERPLATE',
        name='newsletterblocktype',
    )
    newsletter_block_type.create(op.get_bind(), checkfirst=True)

    op.add_column(
        'content_items',
        sa.Column('block_type', newsletter_block_type, nullable=True),
    )
    op.create_index(op.f('ix_content_items_block_type'), 'content_items', ['block_type'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_content_items_block_type'), table_name='content_items')
    op.drop_column('content_items', 'block_type')
    op.execute("DROP TYPE IF EXISTS newsletterblocktype")

    op.drop_index(op.f('ix_content_items_key_maker_id'), table_name='content_items')
    op.drop_constraint('fk_content_items_key_maker_id', 'content_items', type_='foreignkey')
    op.drop_column('content_items', 'key_maker_id')

    # NOTE: Postgres doesn't support removing enum values, so 'NEWSLETTER_BLOCK'
    # stays in the contenttype enum even on downgrade. Not removing event_id's
    # NOT NULL either (can't safely reintroduce it without knowing which rows
    # would violate it) — downgrade leaves event_id nullable.
