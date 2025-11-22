"""Create wallet_transaction_event table

Revision ID: 20251121_081650
Revises: 20251121_073320
Create Date: 2025-11-21 08:16:50

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251121_081650'
down_revision = '20251121_073320'
branch_labels = None
depends_on = None

# Define enum instances at module level with create_type=False
wallet_provider_enum = sa.Enum('fincra', 'paystack', 'flutterwave', name='wallet_provider', create_type=False)
wallet_event_type_enum = sa.Enum(
    'deposit',
    'withdrawal',
    'transfer_in',
    'transfer_out',
    'fee',
    'refund',
    'hold',
    'release',
    name='wallet_event_type',
    create_type=False
)


def upgrade() -> None:
    """Create wallet_transaction_event table with indexes and constraints."""
    # Create enum types before using them in tables
    wallet_provider_enum.create(op.get_bind(), checkfirst=True)
    wallet_event_type_enum.create(op.get_bind(), checkfirst=True)

    # Create wallet_transaction_event table
    op.create_table(
        'wallet_transaction_event',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('external_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('wallet_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider', wallet_provider_enum, nullable=False),
        sa.Column('event_type', wallet_event_type_enum, nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False),
        sa.Column('provider_event_id', sa.String(length=255), nullable=True),
        sa.Column('idempotency_key', sa.String(length=255), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('occurred_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for fast lookups
    op.create_index(
        'ix_wallet_transaction_event_external_id',
        'wallet_transaction_event',
        ['external_id'],
        unique=True
    )
    op.create_index(
        'ix_wallet_transaction_event_wallet_id',
        'wallet_transaction_event',
        ['wallet_id']
    )
    op.create_index(
        'ix_wallet_transaction_event_occurred_at',
        'wallet_transaction_event',
        ['occurred_at']
    )
    op.create_index(
        'ix_wallet_transaction_event_provider_event_id',
        'wallet_transaction_event',
        ['provider_event_id']
    )
    op.create_index(
        'ix_wallet_transaction_event_idempotency_key',
        'wallet_transaction_event',
        ['idempotency_key'],
        unique=True
    )

    # Create composite index for provider + provider_event_id lookups
    op.create_index(
        'ix_wallet_transaction_event_provider_provider_event_id',
        'wallet_transaction_event',
        ['provider', 'provider_event_id']
    )

    # Create composite index for wallet_id + occurred_at for efficient querying
    op.create_index(
        'ix_wallet_transaction_event_wallet_id_occurred_at',
        'wallet_transaction_event',
        ['wallet_id', 'occurred_at']
    )


def downgrade() -> None:
    """Drop wallet_transaction_event table and indexes."""
    op.drop_index('ix_wallet_transaction_event_wallet_id_occurred_at', table_name='wallet_transaction_event')
    op.drop_index('ix_wallet_transaction_event_provider_provider_event_id', table_name='wallet_transaction_event')
    op.drop_index('ix_wallet_transaction_event_idempotency_key', table_name='wallet_transaction_event')
    op.drop_index('ix_wallet_transaction_event_provider_event_id', table_name='wallet_transaction_event')
    op.drop_index('ix_wallet_transaction_event_occurred_at', table_name='wallet_transaction_event')
    op.drop_index('ix_wallet_transaction_event_wallet_id', table_name='wallet_transaction_event')
    op.drop_index('ix_wallet_transaction_event_external_id', table_name='wallet_transaction_event')
    op.drop_table('wallet_transaction_event')
    
    # Drop enum types after dropping table
    wallet_event_type_enum.drop(op.get_bind(), checkfirst=True)
    wallet_provider_enum.drop(op.get_bind(), checkfirst=True)
