"""create_wallet_registry_constraints

Revision ID: 20251120_140218
Revises: d8311371c01f
Create Date: 2025-11-20 14:02:18.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251120_140218'
down_revision: Union[str, None] = 'd8311371c01f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add idempotency_key column and unique constraints for wallet_registry.
    This migration adds:
    1. idempotency_key column for duplicate request prevention
    2. Unique constraint on (user_id, provider, provider_account_id) for wallet uniqueness
    """
    
    # Add idempotency_key column
    op.add_column(
        'wallet_registry',
        sa.Column('idempotency_key', sa.String(length=255), nullable=True)
    )
    
    # Create index on idempotency_key for fast lookups
    op.create_index(
        'ix_wallet_registry_idempotency_key',
        'wallet_registry',
        ['idempotency_key'],
        unique=True,
        postgresql_where=sa.text('idempotency_key IS NOT NULL')  # Partial index for non-null values
    )
    
    # Create unique constraint on (user_id, provider, provider_account_id)
    # This ensures one wallet per user per provider per account
    op.create_unique_constraint(
        'uq_wallet_registry_user_provider_account',
        'wallet_registry',
        ['user_id', 'provider', 'provider_account_id']
    )


def downgrade() -> None:
    """
    Remove idempotency_key column and unique constraints.
    """
    # Drop unique constraint
    op.drop_constraint(
        'uq_wallet_registry_user_provider_account',
        'wallet_registry',
        type_='unique'
    )
    
    # Drop idempotency_key index
    op.drop_index(
        'ix_wallet_registry_idempotency_key',
        table_name='wallet_registry'
    )
    
    # Drop idempotency_key column
    op.drop_column('wallet_registry', 'idempotency_key')
