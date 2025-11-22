"""add_user_role_field

Revision ID: db82de06f57d
Revises: 65ed9294ba55
Create Date: 2025-11-10 08:57:56.503728

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'db82de06f57d'
down_revision: Union[str, None] = '65ed9294ba55'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Define enum instance at module level with create_type=False
user_role_enum = sa.Enum('admin', 'client', 'freelancer', name='userrole', create_type=False)


def upgrade() -> None:
    # Create user_role enum type
    user_role_enum.create(op.get_bind(), checkfirst=True)
    
    # Add role column to users table with default value 'client'
    op.add_column('users', sa.Column('role', user_role_enum, nullable=False, server_default='client'))


def downgrade() -> None:
    # Drop role column
    op.drop_column('users', 'role')
    
    # Drop user_role enum type after dropping column
    user_role_enum.drop(op.get_bind(), checkfirst=True)
