"""ensure status column exists

Revision ID: aaaaaaaaaaaa
Revises: 1f6b479704f4
Create Date: 2026-05-06 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'aaaaaaaaaaaa'
down_revision: Union[str, Sequence[str], None] = '1f6b479704f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    postgresql.ENUM('pending', 'approved', 'rejected', name='psychologist_profile_enum').create(op.get_bind(), checkfirst=True)
    op.execute(sa.text("""
        ALTER TABLE psychologist_profiles 
        ADD COLUMN IF NOT EXISTS status psychologist_profile_enum DEFAULT 'pending'
    """))

def downgrade() -> None:
    op.execute(sa.text("ALTER TABLE psychologist_profiles DROP COLUMN IF EXISTS status"))
