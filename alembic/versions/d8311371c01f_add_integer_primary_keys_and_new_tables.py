"""add_integer_primary_keys_and_new_tables

Revision ID: d8311371c01f
Revises: 4c876238cdeb
Create Date: 2025-11-20 12:56:30.316126

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

wallet_provider_enum = sa.Enum('fincra', 'paystack', 'flutterwave', name='wallet_provider', create_type=False)
hold_status_enum = sa.Enum('active', 'released', 'captured', name='hold_status')
ledger_transaction_type_enum = sa.Enum('debit', 'credit', name='ledger_transaction_type')


# revision identifiers, used by Alembic.
revision: str = 'd8311371c01f'
down_revision: Union[str, None] = '4c876238cdeb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add integer primary keys to core tables and create new tables.
    This is an additive migration that preserves existing UUIDs.
    """
    
    # Create enum type if not present (use a separate instance for creation)
    wallet_provider_enum_type = sa.Enum('fincra', 'paystack', 'flutterwave', name='wallet_provider')
    wallet_provider_enum_type.create(op.get_bind(), checkfirst=True)
    hold_status_enum.create(op.get_bind(), checkfirst=True)
    ledger_transaction_type_enum.create(op.get_bind(), checkfirst=True)
    
    # Step 1: Modify users table to add integer id as a new column (external_id to be added later)
    # For now, we add a new integer id column alongside the existing UUID id
    # In a future migration, we'll rename UUID id to external_id and make integer id the primary key
    op.add_column('users', sa.Column('integer_id', sa.BigInteger(), autoincrement=True, nullable=True))
    # Create a sequence for the integer_id
    op.execute("CREATE SEQUENCE users_integer_id_seq")
    op.execute("ALTER TABLE users ALTER COLUMN integer_id SET DEFAULT nextval('users_integer_id_seq')")
    # Backfill existing rows with sequential IDs
    op.execute("UPDATE users SET integer_id = nextval('users_integer_id_seq')")
    # Make it not nullable and unique
    op.alter_column('users', 'integer_id', nullable=False)
    op.create_index('ix_users_integer_id', 'users', ['integer_id'], unique=True)
    
    # Step 2: Create link_tokens table
    op.create_table(
        'link_tokens',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('external_id', UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('provider', wallet_provider_enum, nullable=False),
        sa.Column('is_consumed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('consumed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_link_tokens_external_id', 'link_tokens', ['external_id'], unique=True)
    op.create_index('ix_link_tokens_user_id', 'link_tokens', ['user_id'], unique=False)
    op.create_index('ix_link_tokens_token', 'link_tokens', ['token'], unique=True)
    
    # Step 3: Create wallet_registry table
    op.create_table(
        'wallet_registry',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('external_id', UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('provider', wallet_provider_enum, nullable=False),
        sa.Column('provider_account_id', sa.String(length=255), nullable=False),
        sa.Column('provider_customer_id', sa.String(length=255), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_wallet_registry_external_id', 'wallet_registry', ['external_id'], unique=True)
    op.create_index('ix_wallet_registry_user_id', 'wallet_registry', ['user_id'], unique=False)
    
    # Step 4: Create holds table
    op.create_table(
        'holds',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('external_id', UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('status', hold_status_enum, nullable=False, server_default='active'),
        sa.Column('reference', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('released_at', sa.DateTime(), nullable=True),
        sa.Column('captured_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_holds_external_id', 'holds', ['external_id'], unique=True)
    op.create_index('ix_holds_user_id', 'holds', ['user_id'], unique=False)
    op.create_index('ix_holds_reference', 'holds', ['reference'], unique=True)
    
    # Step 5: Create ledger_entries table
    op.create_table(
        'ledger_entries',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('external_id', UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('transaction_type', ledger_transaction_type_enum, nullable=False),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('balance_after', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('reference', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_ledger_entries_external_id', 'ledger_entries', ['external_id'], unique=True)
    op.create_index('ix_ledger_entries_user_id', 'ledger_entries', ['user_id'], unique=False)
    op.create_index('ix_ledger_entries_reference', 'ledger_entries', ['reference'], unique=False)
    op.create_index('ix_ledger_entries_created_at', 'ledger_entries', ['created_at'], unique=False)


def downgrade() -> None:
    """
    Remove the integer primary keys and new tables.
    """
    # Drop new tables
    op.drop_index('ix_ledger_entries_created_at', table_name='ledger_entries')
    op.drop_index('ix_ledger_entries_reference', table_name='ledger_entries')
    op.drop_index('ix_ledger_entries_user_id', table_name='ledger_entries')
    op.drop_index('ix_ledger_entries_external_id', table_name='ledger_entries')
    op.drop_table('ledger_entries')
    
    op.drop_index('ix_holds_reference', table_name='holds')
    op.drop_index('ix_holds_user_id', table_name='holds')
    op.drop_index('ix_holds_external_id', table_name='holds')
    op.drop_table('holds')
    
    op.drop_index('ix_wallet_registry_user_id', table_name='wallet_registry')
    op.drop_index('ix_wallet_registry_external_id', table_name='wallet_registry')
    op.drop_table('wallet_registry')
    
    op.drop_index('ix_link_tokens_token', table_name='link_tokens')
    op.drop_index('ix_link_tokens_user_id', table_name='link_tokens')
    op.drop_index('ix_link_tokens_external_id', table_name='link_tokens')
    op.drop_table('link_tokens')
    
    # Remove integer_id from users table
    op.drop_index('ix_users_integer_id', table_name='users')
    op.drop_column('users', 'integer_id')
    op.execute("DROP SEQUENCE IF EXISTS users_integer_id_seq")
    
    # Drop enums after dropping tables
    ledger_transaction_type_enum.drop(op.get_bind(), checkfirst=True)
    hold_status_enum.drop(op.get_bind(), checkfirst=True)
    wallet_provider_enum_type = sa.Enum('fincra', 'paystack', 'flutterwave', name='wallet_provider')
    wallet_provider_enum_type.drop(op.get_bind(), checkfirst=True)

