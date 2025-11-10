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


def upgrade() -> None:
    # Create user_role enum type
    op.execute("CREATE TYPE userrole AS ENUM ('admin', 'client', 'freelancer')")
    
    # Add role column to users table with default value 'client'
    op.add_column('users', sa.Column('role', sa.Enum('admin', 'client', 'freelancer', name='userrole'), nullable=False, server_default='client'))


def downgrade() -> None:
    # Drop role column
    op.drop_column('users', 'role')
    
    # Drop user_role enum type
    op.execute("DROP TYPE userrole")
