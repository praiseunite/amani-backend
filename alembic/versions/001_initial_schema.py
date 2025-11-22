"""Initial schema with proper enum handling

Revision ID: 001_initial_schema
Revises: 
Create Date: 2025-11-22 10:00:00.000000

This migration creates all tables with proper enum handling:
- All PostgreSQL ENUM types are created as top-level instances
- ENUMs are created with checkfirst=True before table creation
- ENUMs are dropped with checkfirst=True after table drops in downgrade
- Migration is idempotent and can be run multiple times safely
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Define all PostgreSQL ENUM types as top-level instances
# This ensures proper enum handling and prevents inline enum creation issues
user_role_enum = postgresql.ENUM('admin', 'client', 'freelancer', name='userrole', create_type=False)
hold_status_enum = postgresql.ENUM('active', 'released', 'captured', name='holdstatus', create_type=False)
kyc_type_enum = postgresql.ENUM('kyc', 'kyb', name='kyctype', create_type=False)
kyc_status_enum = postgresql.ENUM('pending', 'approved', 'rejected', name='kycstatus', create_type=False)
ledger_transaction_type_enum = postgresql.ENUM('debit', 'credit', name='transactiontype', create_type=False)
wallet_provider_enum = postgresql.ENUM('fincra', 'paystack', 'flutterwave', name='walletprovider', create_type=False)
milestone_status_enum = postgresql.ENUM(
    'pending', 'in_progress', 'completed', 'approved', 'rejected', 'disputed',
    name='milestone_status', create_type=False
)
project_status_enum = postgresql.ENUM(
    'draft', 'pending', 'active', 'in_progress', 'completed', 'disputed', 'cancelled', 'refunded',
    name='project_status', create_type=False
)
transaction_type_enum = postgresql.ENUM(
    'deposit', 'withdrawal', 'escrow_hold', 'escrow_release', 'refund', 'fee', 'commission',
    name='transaction_type', create_type=False
)
transaction_status_enum = postgresql.ENUM(
    'pending', 'processing', 'completed', 'failed', 'cancelled', 'refunded',
    name='transaction_status', create_type=False
)


def upgrade() -> None:
    """
    Create all tables and enums for the initial schema.
    Uses checkfirst=True for idempotency.
    """
    # Enable UUID extension for PostgreSQL
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # Create all enum types first (before tables that reference them)
    # Using checkfirst=True makes the migration idempotent
    user_role_enum.create(op.get_bind(), checkfirst=True)
    hold_status_enum.create(op.get_bind(), checkfirst=True)
    kyc_type_enum.create(op.get_bind(), checkfirst=True)
    kyc_status_enum.create(op.get_bind(), checkfirst=True)
    ledger_transaction_type_enum.create(op.get_bind(), checkfirst=True)
    wallet_provider_enum.create(op.get_bind(), checkfirst=True)
    milestone_status_enum.create(op.get_bind(), checkfirst=True)
    project_status_enum.create(op.get_bind(), checkfirst=True)
    transaction_type_enum.create(op.get_bind(), checkfirst=True)
    transaction_status_enum.create(op.get_bind(), checkfirst=True)

    # Create users table first (referenced by other tables)
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('integer_id', sa.BigInteger(), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('phone_number', sa.String(length=50), nullable=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=True),
        sa.Column('role', user_role_enum, nullable=False, server_default='client'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('otp_code', sa.String(length=6), nullable=True),
        sa.Column('otp_expires_at', sa.DateTime(), nullable=True),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('integer_id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)
    op.create_index(op.f('ix_users_integer_id'), 'users', ['integer_id'], unique=False)

    # Create projects table (references users)
    op.create_table(
        'projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('total_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('status', project_status_enum, nullable=False, server_default='draft'),
        sa.Column('creator_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('buyer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('seller_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('terms_accepted_at', sa.DateTime(), nullable=True),
        sa.Column('completion_criteria', sa.Text(), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['buyer_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['seller_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projects_buyer_id'), 'projects', ['buyer_id'], unique=False)
    op.create_index(op.f('ix_projects_creator_id'), 'projects', ['creator_id'], unique=False)
    op.create_index(op.f('ix_projects_seller_id'), 'projects', ['seller_id'], unique=False)
    op.create_index(op.f('ix_projects_status'), 'projects', ['status'], unique=False)

    # Create transactions table (references users and projects)
    op.create_table(
        'transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('transaction_type', transaction_type_enum, nullable=False),
        sa.Column('status', transaction_status_enum, nullable=False, server_default='pending'),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('fee', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0'),
        sa.Column('net_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('payment_gateway', sa.String(length=50), nullable=True, server_default='fincra'),
        sa.Column('gateway_transaction_id', sa.String(length=255), nullable=True),
        sa.Column('gateway_reference', sa.String(length=255), nullable=True),
        sa.Column('gateway_response', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('extra_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('gateway_transaction_id')
    )
    op.create_index(op.f('ix_transactions_gateway_transaction_id'), 'transactions', ['gateway_transaction_id'], unique=False)
    op.create_index(op.f('ix_transactions_project_id'), 'transactions', ['project_id'], unique=False)
    op.create_index(op.f('ix_transactions_status'), 'transactions', ['status'], unique=False)
    op.create_index(op.f('ix_transactions_transaction_type'), 'transactions', ['transaction_type'], unique=False)
    op.create_index(op.f('ix_transactions_user_id'), 'transactions', ['user_id'], unique=False)

    # Create milestones table (references projects)
    op.create_table(
        'milestones',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('status', milestone_status_enum, nullable=False, server_default='pending'),
        sa.Column('is_paid', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('completion_criteria', sa.Text(), nullable=True),
        sa.Column('completion_notes', sa.Text(), nullable=True),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_milestones_project_id'), 'milestones', ['project_id'], unique=False)
    op.create_index(op.f('ix_milestones_status'), 'milestones', ['status'], unique=False)

    # Create kyc table (references users)
    op.create_table(
        'kyc',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', kyc_type_enum, nullable=False, server_default='kyc'),
        sa.Column('nin_or_passport', sa.String(length=100), nullable=False),
        sa.Column('fingerprint', sa.LargeBinary(), nullable=True),
        sa.Column('security_code', sa.String(length=255), nullable=False),
        sa.Column('approval_code', sa.String(length=255), nullable=True),
        sa.Column('image', sa.LargeBinary(), nullable=True),
        sa.Column('status', kyc_status_enum, nullable=False, server_default='pending'),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_kyc_nin_or_passport'), 'kyc', ['nin_or_passport'], unique=False)
    op.create_index(op.f('ix_kyc_status'), 'kyc', ['status'], unique=False)
    op.create_index(op.f('ix_kyc_user_id'), 'kyc', ['user_id'], unique=False)

    # Create holds table
    op.create_table(
        'holds',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('external_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('status', hold_status_enum, nullable=False, server_default='active'),
        sa.Column('reference', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('released_at', sa.DateTime(), nullable=True),
        sa.Column('captured_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('external_id'),
        sa.UniqueConstraint('reference')
    )
    op.create_index(op.f('ix_holds_external_id'), 'holds', ['external_id'], unique=False)
    op.create_index(op.f('ix_holds_reference'), 'holds', ['reference'], unique=False)
    op.create_index(op.f('ix_holds_user_id'), 'holds', ['user_id'], unique=False)

    # Create ledger_entries table
    op.create_table(
        'ledger_entries',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('external_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('transaction_type', ledger_transaction_type_enum, nullable=False),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('balance_after', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('reference', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('external_id')
    )
    op.create_index(op.f('ix_ledger_entries_created_at'), 'ledger_entries', ['created_at'], unique=False)
    op.create_index(op.f('ix_ledger_entries_external_id'), 'ledger_entries', ['external_id'], unique=False)
    op.create_index(op.f('ix_ledger_entries_reference'), 'ledger_entries', ['reference'], unique=False)
    op.create_index(op.f('ix_ledger_entries_user_id'), 'ledger_entries', ['user_id'], unique=False)

    # Create link_tokens table
    op.create_table(
        'link_tokens',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('external_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('provider', wallet_provider_enum, nullable=False),
        sa.Column('is_consumed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('consumed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('external_id'),
        sa.UniqueConstraint('token')
    )
    op.create_index(op.f('ix_link_tokens_external_id'), 'link_tokens', ['external_id'], unique=False)
    op.create_index(op.f('ix_link_tokens_token'), 'link_tokens', ['token'], unique=False)
    op.create_index(op.f('ix_link_tokens_user_id'), 'link_tokens', ['user_id'], unique=False)

    # Create wallet_registry table
    op.create_table(
        'wallet_registry',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('external_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider', wallet_provider_enum, nullable=False),
        sa.Column('provider_account_id', sa.String(length=255), nullable=False),
        sa.Column('provider_customer_id', sa.String(length=255), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('external_id')
    )
    op.create_index(op.f('ix_wallet_registry_external_id'), 'wallet_registry', ['external_id'], unique=False)
    op.create_index(op.f('ix_wallet_registry_user_id'), 'wallet_registry', ['user_id'], unique=False)

    # Create wallet_balance_snapshot table
    op.create_table(
        'wallet_balance_snapshot',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('wallet_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider', wallet_provider_enum, nullable=False),
        sa.Column('balance', sa.Numeric(precision=20, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('external_balance_id', sa.String(length=255), nullable=True),
        sa.Column('as_of', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('idempotency_key', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('external_balance_id'),
        sa.UniqueConstraint('idempotency_key')
    )
    op.create_index(op.f('ix_wallet_balance_snapshot_external_balance_id'), 'wallet_balance_snapshot', ['external_balance_id'], unique=False)
    op.create_index(op.f('ix_wallet_balance_snapshot_id'), 'wallet_balance_snapshot', ['id'], unique=False)
    op.create_index(op.f('ix_wallet_balance_snapshot_idempotency_key'), 'wallet_balance_snapshot', ['idempotency_key'], unique=False)
    op.create_index(op.f('ix_wallet_balance_snapshot_provider'), 'wallet_balance_snapshot', ['provider'], unique=False)
    op.create_index(op.f('ix_wallet_balance_snapshot_wallet_id'), 'wallet_balance_snapshot', ['wallet_id'], unique=False)


def downgrade() -> None:
    """
    Drop all tables and enums in reverse order.
    Uses checkfirst=True for idempotency.
    """
    # Drop tables in reverse order (respecting foreign key dependencies)
    op.drop_index(op.f('ix_wallet_balance_snapshot_wallet_id'), table_name='wallet_balance_snapshot')
    op.drop_index(op.f('ix_wallet_balance_snapshot_provider'), table_name='wallet_balance_snapshot')
    op.drop_index(op.f('ix_wallet_balance_snapshot_idempotency_key'), table_name='wallet_balance_snapshot')
    op.drop_index(op.f('ix_wallet_balance_snapshot_id'), table_name='wallet_balance_snapshot')
    op.drop_index(op.f('ix_wallet_balance_snapshot_external_balance_id'), table_name='wallet_balance_snapshot')
    op.drop_table('wallet_balance_snapshot')

    op.drop_index(op.f('ix_wallet_registry_user_id'), table_name='wallet_registry')
    op.drop_index(op.f('ix_wallet_registry_external_id'), table_name='wallet_registry')
    op.drop_table('wallet_registry')

    op.drop_index(op.f('ix_link_tokens_user_id'), table_name='link_tokens')
    op.drop_index(op.f('ix_link_tokens_token'), table_name='link_tokens')
    op.drop_index(op.f('ix_link_tokens_external_id'), table_name='link_tokens')
    op.drop_table('link_tokens')

    op.drop_index(op.f('ix_ledger_entries_user_id'), table_name='ledger_entries')
    op.drop_index(op.f('ix_ledger_entries_reference'), table_name='ledger_entries')
    op.drop_index(op.f('ix_ledger_entries_external_id'), table_name='ledger_entries')
    op.drop_index(op.f('ix_ledger_entries_created_at'), table_name='ledger_entries')
    op.drop_table('ledger_entries')

    op.drop_index(op.f('ix_holds_user_id'), table_name='holds')
    op.drop_index(op.f('ix_holds_reference'), table_name='holds')
    op.drop_index(op.f('ix_holds_external_id'), table_name='holds')
    op.drop_table('holds')

    op.drop_index(op.f('ix_kyc_user_id'), table_name='kyc')
    op.drop_index(op.f('ix_kyc_status'), table_name='kyc')
    op.drop_index(op.f('ix_kyc_nin_or_passport'), table_name='kyc')
    op.drop_table('kyc')

    op.drop_index(op.f('ix_milestones_status'), table_name='milestones')
    op.drop_index(op.f('ix_milestones_project_id'), table_name='milestones')
    op.drop_table('milestones')

    op.drop_index(op.f('ix_transactions_user_id'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_transaction_type'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_status'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_project_id'), table_name='transactions')
    op.drop_index(op.f('ix_transactions_gateway_transaction_id'), table_name='transactions')
    op.drop_table('transactions')

    op.drop_index(op.f('ix_projects_status'), table_name='projects')
    op.drop_index(op.f('ix_projects_seller_id'), table_name='projects')
    op.drop_index(op.f('ix_projects_creator_id'), table_name='projects')
    op.drop_index(op.f('ix_projects_buyer_id'), table_name='projects')
    op.drop_table('projects')

    op.drop_index(op.f('ix_users_integer_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')

    # Drop all enum types after all related tables are dropped
    # Using checkfirst=True makes the migration idempotent
    transaction_status_enum.drop(op.get_bind(), checkfirst=True)
    transaction_type_enum.drop(op.get_bind(), checkfirst=True)
    project_status_enum.drop(op.get_bind(), checkfirst=True)
    milestone_status_enum.drop(op.get_bind(), checkfirst=True)
    wallet_provider_enum.drop(op.get_bind(), checkfirst=True)
    ledger_transaction_type_enum.drop(op.get_bind(), checkfirst=True)
    kyc_status_enum.drop(op.get_bind(), checkfirst=True)
    kyc_type_enum.drop(op.get_bind(), checkfirst=True)
    hold_status_enum.drop(op.get_bind(), checkfirst=True)
    user_role_enum.drop(op.get_bind(), checkfirst=True)
