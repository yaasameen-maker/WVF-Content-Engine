"""add approver email and passcode reset tokens

Revision ID: a4d9c6e2b8f1
Revises: f3b8d1e6a9c2
Create Date: 2026-09-02 00:00:00.000000

Enables self-service "forgot passcode" for Nancy/Maria instead of
needing manage_approvers.py reset run against production every time —
see app/models/approver.py's PasscodeResetToken docstring.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a4d9c6e2b8f1'
down_revision: Union[str, None] = 'f3b8d1e6a9c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('approvers', sa.Column('email', sa.String(length=255), nullable=True))
    op.create_unique_constraint('uq_approvers_email', 'approvers', ['email'])

    op.create_table(
        'passcode_reset_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('approver_id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['approver_id'], ['approvers.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_passcode_reset_tokens_id'), 'passcode_reset_tokens', ['id'], unique=False
    )
    op.create_index(
        op.f('ix_passcode_reset_tokens_approver_id'), 'passcode_reset_tokens', ['approver_id'], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_passcode_reset_tokens_approver_id'), table_name='passcode_reset_tokens')
    op.drop_index(op.f('ix_passcode_reset_tokens_id'), table_name='passcode_reset_tokens')
    op.drop_table('passcode_reset_tokens')

    op.drop_constraint('uq_approvers_email', 'approvers', type_='unique')
    op.drop_column('approvers', 'email')
