"""create approvers table, add approved_by_id to content_items

Revision ID: f3b8d1e6a9c2
Revises: e1c7a3f9d2b5
Create Date: 2026-09-01 00:00:00.000000

Minimal per-person passcode gate on the Approve action — see
app/models/approver.py's module docstring for why. Does not create any
rows; use backend/manage_approvers.py after this migration to create
Nancy/Maria's actual approver accounts (their real passcodes are
generated at runtime and shown once, never committed to this repo).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3b8d1e6a9c2'
down_revision: Union[str, None] = 'e1c7a3f9d2b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'approvers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('passcode_hash', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_index(op.f('ix_approvers_id'), 'approvers', ['id'], unique=False)

    op.add_column('content_items', sa.Column('approved_by_id', sa.Integer(), nullable=True))
    op.create_index(
        op.f('ix_content_items_approved_by_id'), 'content_items', ['approved_by_id'], unique=False
    )
    op.create_foreign_key(
        'fk_content_items_approved_by_id_approvers',
        'content_items', 'approvers',
        ['approved_by_id'], ['id'],
    )


def downgrade() -> None:
    op.drop_constraint('fk_content_items_approved_by_id_approvers', 'content_items', type_='foreignkey')
    op.drop_index(op.f('ix_content_items_approved_by_id'), table_name='content_items')
    op.drop_column('content_items', 'approved_by_id')

    op.drop_index(op.f('ix_approvers_id'), table_name='approvers')
    op.drop_table('approvers')
