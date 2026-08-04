"""create key_makers_private table

Revision ID: e2b8f6c1a4d7
Revises: c7d4e1a9f2b3
Create Date: 2026-08-03 00:00:00.000001

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e2b8f6c1a4d7'
down_revision: Union[str, None] = 'c7d4e1a9f2b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'key_makers_private',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key_maker_id', sa.Integer(), nullable=False),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('team_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['key_maker_id'], ['key_makers.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key_maker_id'),
    )
    op.create_index(op.f('ix_key_makers_private_id'), 'key_makers_private', ['id'], unique=False)
    op.create_index(op.f('ix_key_makers_private_key_maker_id'), 'key_makers_private', ['key_maker_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_key_makers_private_key_maker_id'), table_name='key_makers_private')
    op.drop_index(op.f('ix_key_makers_private_id'), table_name='key_makers_private')
    op.drop_table('key_makers_private')
