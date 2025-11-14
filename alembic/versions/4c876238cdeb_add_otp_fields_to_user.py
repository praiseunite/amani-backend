"""add_otp_fields_to_user

Revision ID: 4c876238cdeb
Revises: 59cafc4477ac
Create Date: 2025-11-14 08:13:15.173421

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4c876238cdeb'
down_revision: Union[str, None] = '59cafc4477ac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add OTP fields to users table
    op.add_column('users', sa.Column('otp_code', sa.String(6), nullable=True))
    op.add_column('users', sa.Column('otp_expires_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Remove OTP fields from users table
    op.drop_column('users', 'otp_expires_at')
    op.drop_column('users', 'otp_code')
