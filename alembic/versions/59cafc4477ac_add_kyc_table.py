"""add_kyc_table

Revision ID: 59cafc4477ac
Revises: db82de06f57d
Create Date: 2025-11-10 12:57:10.875413

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '59cafc4477ac'
down_revision: Union[str, None] = 'db82de06f57d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create kyc_type and kyc_status enum types
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE kyctype AS ENUM ('kyc', 'kyb');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE kycstatus AS ENUM ('pending', 'approved', 'rejected');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Create kyc table
    op.create_table(
        'kyc',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', postgresql.ENUM('kyc', 'kyb', name='kyctype', create_type=False), nullable=False, server_default='kyc'),
        sa.Column('nin_or_passport', sa.String(length=100), nullable=False),
        sa.Column('fingerprint', sa.LargeBinary(), nullable=True),
        sa.Column('security_code', sa.String(length=255), nullable=False),
        sa.Column('approval_code', sa.String(length=255), nullable=True),
        sa.Column('image', sa.LargeBinary(), nullable=True),
        sa.Column('status', postgresql.ENUM('pending', 'approved', 'rejected', name='kycstatus', create_type=False), nullable=False, server_default='pending'),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_kyc_user_id'), 'kyc', ['user_id'], unique=False)
    op.create_index(op.f('ix_kyc_nin_or_passport'), 'kyc', ['nin_or_passport'], unique=False)
    op.create_index(op.f('ix_kyc_status'), 'kyc', ['status'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_kyc_status'), table_name='kyc')
    op.drop_index(op.f('ix_kyc_nin_or_passport'), table_name='kyc')
    op.drop_index(op.f('ix_kyc_user_id'), table_name='kyc')
    
    # Drop kyc table
    op.drop_table('kyc')
    
    # Drop enum types after dropping table
    op.execute('DROP TYPE IF EXISTS kycstatus')
    op.execute('DROP TYPE IF EXISTS kyctype')

