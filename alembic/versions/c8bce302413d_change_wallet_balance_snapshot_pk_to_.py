"""Change wallet_balance_snapshot PK to UUID and remove external_id

Revision ID: c8bce302413d
Revises: b4ae3e96c066
Create Date: 2025-11-22 08:23:37.749247

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8bce302413d'
down_revision: Union[str, None] = 'b4ae3e96c066'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
