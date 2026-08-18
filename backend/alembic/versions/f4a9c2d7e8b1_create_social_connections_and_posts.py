"""create social_connections, social_posts, and oauth_pkce_states tables

Revision ID: f4a9c2d7e8b1
Revises: d3a5b8e0c9f1
Create Date: 2026-08-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f4a9c2d7e8b1'
down_revision: Union[str, None] = 'd3a5b8e0c9f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    social_platform_enum = sa.Enum('x', name='socialplatform')

    op.create_table(
        'social_connections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('platform', social_platform_enum, nullable=False),
        sa.Column('platform_account_id', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('access_token_encrypted', sa.Text(), nullable=False),
        sa.Column('refresh_token_encrypted', sa.Text(), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(), nullable=True),
        sa.Column('scopes', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_social_connections_id'), 'social_connections', ['id'], unique=False
    )
    op.create_index(
        op.f('ix_social_connections_platform'), 'social_connections', ['platform'], unique=False
    )

    op.create_table(
        'social_posts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('content_item_id', sa.Integer(), nullable=False),
        sa.Column('platform', social_platform_enum, nullable=False),
        sa.Column('external_post_id', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('posted_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['content_item_id'], ['content_items.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_social_posts_id'), 'social_posts', ['id'], unique=False)
    op.create_index(
        op.f('ix_social_posts_content_item_id'), 'social_posts', ['content_item_id'], unique=False
    )
    op.create_index(op.f('ix_social_posts_platform'), 'social_posts', ['platform'], unique=False)

    op.create_table(
        'oauth_pkce_states',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('platform', social_platform_enum, nullable=False),
        sa.Column('state', sa.String(length=255), nullable=False),
        sa.Column('code_verifier', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('state'),
    )
    op.create_index(op.f('ix_oauth_pkce_states_id'), 'oauth_pkce_states', ['id'], unique=False)
    op.create_index(
        op.f('ix_oauth_pkce_states_platform'), 'oauth_pkce_states', ['platform'], unique=False
    )
    op.create_index(
        op.f('ix_oauth_pkce_states_state'), 'oauth_pkce_states', ['state'], unique=True
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_oauth_pkce_states_state'), table_name='oauth_pkce_states')
    op.drop_index(op.f('ix_oauth_pkce_states_platform'), table_name='oauth_pkce_states')
    op.drop_index(op.f('ix_oauth_pkce_states_id'), table_name='oauth_pkce_states')
    op.drop_table('oauth_pkce_states')

    op.drop_index(op.f('ix_social_posts_platform'), table_name='social_posts')
    op.drop_index(op.f('ix_social_posts_content_item_id'), table_name='social_posts')
    op.drop_index(op.f('ix_social_posts_id'), table_name='social_posts')
    op.drop_table('social_posts')

    op.drop_index(op.f('ix_social_connections_platform'), table_name='social_connections')
    op.drop_index(op.f('ix_social_connections_id'), table_name='social_connections')
    op.drop_table('social_connections')

    sa.Enum(name='socialplatform').drop(op.get_bind(), checkfirst=True)
