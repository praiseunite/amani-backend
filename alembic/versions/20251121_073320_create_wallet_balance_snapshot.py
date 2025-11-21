"""create_wallet_balance_snapshot_table

Revision ID: 20251121_073320
Revises: 20251120_140218
Create Date: 2025-11-21 07:33:20.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20251121_073320'
down_revision: Union[str, None] = '20251120_140218'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create wallet_balance_snapshot table for tracking wallet balances over time.
    This table stores snapshots of wallet balances at specific points in time
    with idempotency support and constraints to prevent duplicate entries.
    """
    
    # Create wallet_balance_snapshot table
    op.create_table(
        'wallet_balance_snapshot',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('external_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('wallet_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            'provider',
            sa.Enum('fincra', 'paystack', 'flutterwave', name='wallet_provider'),
            nullable=False
        ),
        sa.Column('balance', sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('external_balance_id', sa.String(length=255), nullable=True),
        sa.Column('as_of', sa.DateTime(), nullable=False),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('idempotency_key', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_wallet_balance_snapshot')
    )
    
    # Create indexes
    op.create_index(
        'ix_wallet_balance_snapshot_external_id',
        'wallet_balance_snapshot',
        ['external_id'],
        unique=True
    )
    
    op.create_index(
        'ix_wallet_balance_snapshot_wallet_id',
        'wallet_balance_snapshot',
        ['wallet_id']
    )
    
    op.create_index(
        'ix_wallet_balance_snapshot_provider',
        'wallet_balance_snapshot',
        ['provider']
    )
    
    op.create_index(
        'ix_wallet_balance_snapshot_external_balance_id',
        'wallet_balance_snapshot',
        ['external_balance_id'],
        unique=True,
        postgresql_where=sa.text('external_balance_id IS NOT NULL')
    )
    
    op.create_index(
        'ix_wallet_balance_snapshot_idempotency_key',
        'wallet_balance_snapshot',
        ['idempotency_key'],
        unique=True,
        postgresql_where=sa.text('idempotency_key IS NOT NULL')
    )
    
    # Create unique constraint on (wallet_id, as_of) to prevent duplicate snapshots
    # for the same wallet at the same time
    op.create_unique_constraint(
        'uq_wallet_balance_snapshot_wallet_id_as_of',
        'wallet_balance_snapshot',
        ['wallet_id', 'as_of']
    )


def downgrade() -> None:
    """
    Drop wallet_balance_snapshot table and related constraints.
    """
    # Drop indexes
    op.drop_index(
        'ix_wallet_balance_snapshot_idempotency_key',
        table_name='wallet_balance_snapshot'
    )
    op.drop_index(
        'ix_wallet_balance_snapshot_external_balance_id',
        table_name='wallet_balance_snapshot'
    )
    op.drop_index(
        'ix_wallet_balance_snapshot_provider',
        table_name='wallet_balance_snapshot'
    )
    op.drop_index(
        'ix_wallet_balance_snapshot_wallet_id',
        table_name='wallet_balance_snapshot'
    )
    op.drop_index(
        'ix_wallet_balance_snapshot_external_id',
        table_name='wallet_balance_snapshot'
    )
    
    # Drop table
    op.drop_table('wallet_balance_snapshot')
