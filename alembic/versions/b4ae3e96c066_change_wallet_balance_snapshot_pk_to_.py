"""Change wallet_balance_snapshot PK to UUID and remove external_id

Revision ID: b4ae3e96c066
Revises: aac374a28924
Create Date: 2025-11-22 08:22:30.851309

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b4ae3e96c066'
down_revision: Union[str, None] = 'aac374a28924'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove external_id column
    with op.batch_alter_table('wallet_balance_snapshot') as batch_op:
        batch_op.drop_column('external_id')

    # Change id column to UUID type and set default
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
    op.execute('ALTER TABLE wallet_balance_snapshot ALTER COLUMN id DROP DEFAULT;')
    op.execute('ALTER TABLE wallet_balance_snapshot ALTER COLUMN id TYPE uuid USING uuid_generate_v4();')
    op.execute('ALTER TABLE wallet_balance_snapshot ALTER COLUMN id SET DEFAULT uuid_generate_v4();')


def downgrade() -> None:
    # Downgrade: add external_id column back
    with op.batch_alter_table('wallet_balance_snapshot') as batch_op:
        batch_op.add_column(sa.Column('external_id', sa.dialects.postgresql.UUID(as_uuid=True), unique=True, nullable=False))

    # Change id column back to bigint
    op.execute('ALTER TABLE wallet_balance_snapshot ALTER COLUMN id TYPE bigint USING (CAST(id AS bigint));')
    op.execute('ALTER TABLE wallet_balance_snapshot ALTER COLUMN id DROP DEFAULT;')
