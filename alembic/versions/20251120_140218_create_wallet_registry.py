"""
Alembic migration: create wallet_registry table with unique constraints
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251120_140218_create_wallet_registry'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'wallet_registry',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('provider', sa.String(length=64), nullable=False),
        sa.Column('provider_wallet_id', sa.String(length=255), nullable=False),
        sa.Column('bot_user_id', sa.String(length=128), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('idempotency_key', sa.String(length=255), nullable=True),
    )
    op.create_index('ix_wallet_registry_provider_provider_wallet_id', 'wallet_registry', ['provider', 'provider_wallet_id'], unique=True)
    op.create_index('ix_wallet_registry_idempotency_key', 'wallet_registry', ['idempotency_key'], unique=True)


def downgrade():
    op.drop_index('ix_wallet_registry_idempotency_key', table_name='wallet_registry')
    op.drop_index('ix_wallet_registry_provider_provider_wallet_id', table_name='wallet_registry')
    op.drop_table('wallet_registry')
