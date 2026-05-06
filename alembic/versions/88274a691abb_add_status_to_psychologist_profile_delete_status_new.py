"""add status to PsychologistProfile delete status new

Revision ID: 88274a691abb
Revises: 1c68b51cbfb4
Create Date: 2026-05-05 16:42:41.327389

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '88274a691abb'
down_revision: Union[str, Sequence[str], None] = '1c68b51cbfb4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
