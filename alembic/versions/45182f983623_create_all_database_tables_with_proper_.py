"""Create all database tables with proper ENUM handling

Revision ID: 45182f983623
Revises: c8bce302413d
Create Date: 2025-11-22 08:07:20.804414

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '45182f983623'
down_revision: Union[str, None] = 'c8bce302413d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Define all ENUMs as top-level instances
wallet_provider_enum = postgresql.ENUM('fincra', 'paystack', 'flutterwave', name='wallet_provider')
project_status_enum = postgresql.ENUM('draft', 'pending', 'active', 'in_progress', 'completed', 'disputed', 'cancelled', 'refunded', name='project_status')
milestone_status_enum = postgresql.ENUM('pending', 'in_progress', 'completed', 'approved', 'rejected', 'disputed', name='milestone_status')
transaction_type_enum = postgresql.ENUM('deposit', 'withdrawal', 'escrow_hold', 'escrow_release', 'refund', 'fee', 'commission', name='transaction_type')
transaction_status_enum = postgresql.ENUM('pending', 'processing', 'completed', 'failed', 'cancelled', 'refunded', name='transaction_status')
kyc_type_enum = postgresql.ENUM('kyc', 'kyb', name='kyc_type')
kyc_status_enum = postgresql.ENUM('pending', 'approved', 'rejected', name='kyc_status')
user_role_enum = postgresql.ENUM('admin', 'client', 'freelancer', name='user_role')
hold_status_enum = postgresql.ENUM('active', 'released', 'captured', name='hold_status')
ledger_transaction_type_enum = postgresql.ENUM('debit', 'credit', name='ledger_transaction_type')


def upgrade() -> None:
    # Create all ENUM types BEFORE creating tables
    wallet_provider_enum.create(op.get_bind(), checkfirst=True)
    project_status_enum.create(op.get_bind(), checkfirst=True)
    milestone_status_enum.create(op.get_bind(), checkfirst=True)
    transaction_type_enum.create(op.get_bind(), checkfirst=True)
    transaction_status_enum.create(op.get_bind(), checkfirst=True)
    kyc_type_enum.create(op.get_bind(), checkfirst=True)
    kyc_status_enum.create(op.get_bind(), checkfirst=True)
    user_role_enum.create(op.get_bind(), checkfirst=True)
    hold_status_enum.create(op.get_bind(), checkfirst=True)
    ledger_transaction_type_enum.create(op.get_bind(), checkfirst=True)

    # Create UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('integer_id', sa.BigInteger, unique=True, nullable=True, index=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('phone_number', sa.String(50), nullable=True),
        sa.Column('hashed_password', sa.String(255), nullable=True),
        sa.Column('role', user_role_enum, nullable=False, server_default='client'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default=sa.text('true')),
        sa.Column('is_verified', sa.Boolean, nullable=False, server_default=sa.text('false')),
        sa.Column('is_superuser', sa.Boolean, nullable=False, server_default=sa.text('false')),
        sa.Column('otp_code', sa.String(6), nullable=True),
        sa.Column('otp_expires_at', sa.DateTime, nullable=True),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('bio', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
        sa.Column('last_login', sa.DateTime, nullable=True),
    )

    # Create projects table
    op.create_table(
        'projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('total_amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='USD'),
        sa.Column('status', project_status_enum, nullable=False, server_default='draft', index=True),
        sa.Column('creator_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('buyer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True, index=True),
        sa.Column('seller_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True, index=True),
        sa.Column('terms_accepted_at', sa.DateTime, nullable=True),
        sa.Column('completion_criteria', sa.Text, nullable=True),
        sa.Column('start_date', sa.DateTime, nullable=True),
        sa.Column('due_date', sa.DateTime, nullable=True),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
    )

    # Create milestones table
    op.create_table(
        'milestones',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('order_index', sa.Integer, nullable=False, server_default='0'),
        sa.Column('amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='USD'),
        sa.Column('status', milestone_status_enum, nullable=False, server_default='pending', index=True),
        sa.Column('is_paid', sa.Boolean, nullable=False, server_default=sa.text('false')),
        sa.Column('completion_criteria', sa.Text, nullable=True),
        sa.Column('completion_notes', sa.Text, nullable=True),
        sa.Column('due_date', sa.DateTime, nullable=True),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('approved_at', sa.DateTime, nullable=True),
        sa.Column('paid_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
    )

    # Create transactions table
    op.create_table(
        'transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('transaction_type', transaction_type_enum, nullable=False, index=True),
        sa.Column('status', transaction_status_enum, nullable=False, server_default='pending', index=True),
        sa.Column('amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='USD'),
        sa.Column('fee', sa.Numeric(15, 2), nullable=False, server_default='0'),
        sa.Column('net_amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('payment_gateway', sa.String(50), nullable=True, server_default='fincra'),
        sa.Column('gateway_transaction_id', sa.String(255), nullable=True, unique=True, index=True),
        sa.Column('gateway_reference', sa.String(255), nullable=True),
        sa.Column('gateway_response', postgresql.JSON, nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('extra_data', postgresql.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
        sa.Column('processed_at', sa.DateTime, nullable=True),
        sa.Column('completed_at', sa.DateTime, nullable=True),
    )

    # Create kyc table
    op.create_table(
        'kyc',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('type', kyc_type_enum, nullable=False, server_default='kyc'),
        sa.Column('nin_or_passport', sa.String(100), nullable=False, index=True),
        sa.Column('fingerprint', sa.LargeBinary, nullable=True),
        sa.Column('security_code', sa.String(255), nullable=False),
        sa.Column('approval_code', sa.String(255), nullable=True),
        sa.Column('image', sa.LargeBinary, nullable=True),
        sa.Column('status', kyc_status_enum, nullable=False, server_default='pending', index=True),
        sa.Column('rejection_reason', sa.Text, nullable=True),
        sa.Column('submitted_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
        sa.Column('verified_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
    )

    # Create link_tokens table
    # Note: user_id without FK constraint (will be migrated to integer FK in future per hexagonal architecture)
    op.create_table(
        'link_tokens',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True, nullable=False),
        sa.Column('external_id', postgresql.UUID(as_uuid=True), unique=True, nullable=False, server_default=sa.text('uuid_generate_v4()'), index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),  # No FK - hexagonal architecture design
        sa.Column('token', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('provider', wallet_provider_enum, nullable=False),
        sa.Column('is_consumed', sa.Boolean, nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime, nullable=False),
        sa.Column('consumed_at', sa.DateTime, nullable=True),
    )

    # Create wallet_registry table
    # Note: user_id without FK constraint (will be migrated to integer FK in future per hexagonal architecture)
    op.create_table(
        'wallet_registry',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True, nullable=False),
        sa.Column('external_id', postgresql.UUID(as_uuid=True), unique=True, nullable=False, server_default=sa.text('uuid_generate_v4()'), index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),  # No FK - hexagonal architecture design
        sa.Column('provider', wallet_provider_enum, nullable=False),
        sa.Column('provider_account_id', sa.String(255), nullable=False),
        sa.Column('provider_customer_id', sa.String(255), nullable=True),
        sa.Column('metadata', postgresql.JSON, nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
    )

    # Create holds table
    # Note: user_id without FK constraint (will be migrated to integer FK in future per hexagonal architecture)
    op.create_table(
        'holds',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True, nullable=False),
        sa.Column('external_id', postgresql.UUID(as_uuid=True), unique=True, nullable=False, server_default=sa.text('uuid_generate_v4()'), index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),  # No FK - hexagonal architecture design
        sa.Column('amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='USD'),
        sa.Column('status', hold_status_enum, nullable=False, server_default='active'),
        sa.Column('reference', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
        sa.Column('released_at', sa.DateTime, nullable=True),
        sa.Column('captured_at', sa.DateTime, nullable=True),
    )

    # Create ledger_entries table
    # Note: user_id without FK constraint (will be migrated to integer FK in future per hexagonal architecture)
    op.create_table(
        'ledger_entries',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True, nullable=False),
        sa.Column('external_id', postgresql.UUID(as_uuid=True), unique=True, nullable=False, server_default=sa.text('uuid_generate_v4()'), index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),  # No FK - hexagonal architecture design
        sa.Column('transaction_type', ledger_transaction_type_enum, nullable=False),
        sa.Column('amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='USD'),
        sa.Column('balance_after', sa.Numeric(15, 2), nullable=False),
        sa.Column('reference', sa.String(255), nullable=False, index=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('now()'), index=True),
    )

    # Create wallet_balance_snapshot table
    # Note: wallet_id is a UUID reference without FK constraint (hexagonal architecture design)
    op.create_table(
        'wallet_balance_snapshot',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=sa.text('uuid_generate_v4()'), index=True),
        sa.Column('wallet_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),  # No FK - loosely coupled design
        sa.Column('provider', wallet_provider_enum, nullable=False, index=True),
        sa.Column('balance', sa.Numeric(20, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='USD'),
        sa.Column('external_balance_id', sa.String(255), nullable=True, unique=True, index=True),
        sa.Column('as_of', sa.DateTime, nullable=False, server_default=sa.text('now()')),
        sa.Column('metadata', postgresql.JSON, nullable=True),
        sa.Column('idempotency_key', sa.String(255), nullable=True, unique=True, index=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
    )


def downgrade() -> None:
    # Drop tables in reverse order (respecting foreign key constraints)
    op.drop_table('wallet_balance_snapshot')
    op.drop_table('ledger_entries')
    op.drop_table('holds')
    op.drop_table('wallet_registry')
    op.drop_table('link_tokens')
    op.drop_table('kyc')
    op.drop_table('transactions')
    op.drop_table('milestones')
    op.drop_table('projects')
    op.drop_table('users')

    # Drop all ENUM types AFTER dropping tables
    ledger_transaction_type_enum.drop(op.get_bind(), checkfirst=True)
    hold_status_enum.drop(op.get_bind(), checkfirst=True)
    user_role_enum.drop(op.get_bind(), checkfirst=True)
    kyc_status_enum.drop(op.get_bind(), checkfirst=True)
    kyc_type_enum.drop(op.get_bind(), checkfirst=True)
    transaction_status_enum.drop(op.get_bind(), checkfirst=True)
    transaction_type_enum.drop(op.get_bind(), checkfirst=True)
    milestone_status_enum.drop(op.get_bind(), checkfirst=True)
    project_status_enum.drop(op.get_bind(), checkfirst=True)
    wallet_provider_enum.drop(op.get_bind(), checkfirst=True)
