"""Add uppercase embedding states

Revision ID: b35f99144db8
Revises: 4d2c95081dd2
Create Date: 2026-07-03 12:05:14.020652

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b35f99144db8'
down_revision: Union[str, None] = '4d2c95081dd2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE documentstatus ADD VALUE IF NOT EXISTS 'PARSING'")
        op.execute("ALTER TYPE documentstatus ADD VALUE IF NOT EXISTS 'CHUNKING'")
        op.execute("ALTER TYPE documentstatus ADD VALUE IF NOT EXISTS 'EMBEDDING'")
        op.execute("ALTER TYPE documentstatus ADD VALUE IF NOT EXISTS 'INDEXING'")


def downgrade() -> None:
    pass
