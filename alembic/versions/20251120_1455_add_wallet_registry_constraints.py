"""add_wallet_registry_constraints

Revision ID: 20251120_1455_add_wallet_registry_constraints
Revises: d8311371c01f
Create Date: 2025-11-20 14:55:01.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251120_1455_add_wallet_registry_constraints'
down_revision: Union[str, None] = 'd8311371c01f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Add unique constraints and indexes to wallet_registry table."""
    # Add unique index on (user_id, provider, provider_account_id) for idempotency
    op.create_index(
        'ix_wallet_registry_user_provider_account_unique',
        'wallet_registry',
        ['user_id', 'provider', 'provider_account_id'],
        unique=True,
    )

    # Ensure foreign key to users table (if not already present)
    op.create_foreign_key(
        'fk_wallet_registry_user_id',
        'wallet_registry',
        'users',
        ['user_id'],
        ['id'],
        ondelete='CASCADE',
    )

def downgrade() -> None:
    """Remove constraints."""
    op.drop_constraint('fk_wallet_registry_user_id', 'wallet_registry', type_='foreignkey')
    op.drop_index('ix_wallet_registry_user_provider_account_unique', table_name='wallet_registry')
