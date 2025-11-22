"""add_kyc_table

Revision ID: 59cafc4477ac
Revises: db82de06f57d
Create Date: 2025-11-10 12:57:10.875413

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '59cafc4477ac'
down_revision: Union[str, None] = 'db82de06f57d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Define enum instances at module level with create_type=False
kyc_type_enum = sa.Enum('kyc', 'kyb', name='kyctype', create_type=False)
kyc_status_enum = sa.Enum('pending', 'approved', 'rejected', name='kycstatus', create_type=False)


def upgrade() -> None:
    # Create kyc_type and kyc_status enum types
    kyc_type_enum.create(op.get_bind(), checkfirst=True)
    kyc_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Create kyc table
    op.create_table(
        'kyc',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
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
    kyc_status_enum.drop(op.get_bind(), checkfirst=True)
    kyc_type_enum.drop(op.get_bind(), checkfirst=True)

