"""add status to psycology register remove psychologist_status

Revision ID: 1f6b479704f4
Revises: 7669c05b1afc
Create Date: 2026-05-06 11:08:23.613501

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '1f6b479704f4'
down_revision: Union[str, Sequence[str], None] = '7669c05b1afc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.execute(sa.text("ALTER TABLE psychologist_profiles DROP COLUMN IF EXISTS psychologist_status"))

def downgrade() -> None:
    pass
