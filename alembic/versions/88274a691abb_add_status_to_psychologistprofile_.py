"""add status to PsychologistProfile delete status new

Revision ID: 88274a691abb
Revises: 76936a860621
Create Date: 2026-05-05 16:42:41.327389

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '88274a691abb'
down_revision: Union[str, Sequence[str], None] = '1c68b51cbfb4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text("ALTER TABLE psychologist_profiles DROP COLUMN IF EXISTS status"))
    op.execute(sa.text(
        "ALTER TABLE psychologist_profiles ADD COLUMN status profile_status_enum DEFAULT 'pending'"))


def downgrade() -> None:
    op.execute(
        sa.text("ALTER TABLE psychologist_profiles DROP COLUMN IF EXISTS status"))
    op.execute(sa.text("DROP TYPE IF EXISTS profile_status_enum"))
