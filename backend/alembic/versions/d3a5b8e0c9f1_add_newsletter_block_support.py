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
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == 'sqlite'

    # New enum for which of the 6 modular newsletter sections a row is —
    # created before the batch block below since content_items' new
    # block_type column references it.
    newsletter_block_type = sa.Enum(
        'FEATURE_ARTICLE', 'EVENTS_LIST', 'GRANT_FLYER',
        'TIPS_CTA', 'MEMBER_SPOTLIGHT', 'BOILERPLATE',
        name='newsletterblocktype',
    )
    newsletter_block_type.create(op.get_bind(), checkfirst=True)

    # SQLite has no ALTER COLUMN and can't add constraints to an existing
    # table at all — batch mode recreates the table under the hood
    # instead. All content_items changes must go through ONE batch block
    # (not several sequential ones), since Alembic's SQLite batch mode
    # doesn't reliably clean up its temp table between separate batch
    # contexts within the same migration. Postgres/other dialects use
    # plain alter_column/add_column, which work incrementally as normal.
    if is_sqlite:
        with op.batch_alter_table('content_items') as batch_op:
            # Relax event_id: some newsletter_block rows (boilerplate,
            # grant_flyer, member_spotlight) are reused across issues,
            # not tied to one event.
            batch_op.alter_column('event_id', existing_type=sa.Integer(), nullable=True)
            batch_op.add_column(sa.Column('key_maker_id', sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                'fk_content_items_key_maker_id', 'key_makers', ['key_maker_id'], ['id']
            )
            batch_op.create_index(
                op.f('ix_content_items_key_maker_id'), ['key_maker_id'], unique=False
            )
            batch_op.add_column(sa.Column('block_type', newsletter_block_type, nullable=True))
            batch_op.create_index(
                op.f('ix_content_items_block_type'), ['block_type'], unique=False
            )
    else:
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

        # Extend the content_type enum with the new value. Postgres-only
        # syntax (ALTER TYPE ... ADD VALUE) — SQLite stores the enum as a
        # CHECK constraint via SQLAlchemy's Enum type and doesn't need/
        # support this statement at all, so it only runs here.
        op.execute("ALTER TYPE contenttype ADD VALUE IF NOT EXISTS 'NEWSLETTER_BLOCK'")

        op.add_column(
            'content_items',
            sa.Column('block_type', newsletter_block_type, nullable=True),
        )
        op.create_index(op.f('ix_content_items_block_type'), 'content_items', ['block_type'], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == 'sqlite'

    if is_sqlite:
        with op.batch_alter_table('content_items') as batch_op:
            batch_op.drop_index(op.f('ix_content_items_block_type'))
            batch_op.drop_column('block_type')
            batch_op.drop_index(op.f('ix_content_items_key_maker_id'))
            batch_op.drop_constraint('fk_content_items_key_maker_id', type_='foreignkey')
            batch_op.drop_column('key_maker_id')
    else:
        op.drop_index(op.f('ix_content_items_block_type'), table_name='content_items')
        op.drop_column('content_items', 'block_type')
        op.execute("DROP TYPE IF EXISTS newsletterblocktype")

        op.drop_index(op.f('ix_content_items_key_maker_id'), table_name='content_items')
        op.drop_constraint('fk_content_items_key_maker_id', 'content_items', type_='foreignkey')
        op.drop_column('content_items', 'key_maker_id')

    if is_sqlite:
        newsletter_block_type = sa.Enum(name='newsletterblocktype')
        newsletter_block_type.drop(op.get_bind(), checkfirst=True)

    # NOTE: Postgres doesn't support removing enum values, so 'NEWSLETTER_BLOCK'
    # stays in the contenttype enum even on downgrade. Not removing event_id's
    # NOT NULL either (can't safely reintroduce it without knowing which rows
    # would violate it) — downgrade leaves event_id nullable.
