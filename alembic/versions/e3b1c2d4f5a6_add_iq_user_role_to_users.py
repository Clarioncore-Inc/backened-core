"""add iq user role to users

Revision ID: e3b1c2d4f5a6
Revises: d1f4a7c9b2e3
Create Date: 2026-06-01 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e3b1c2d4f5a6"
down_revision: Union[str, Sequence[str], None] = "d1f4a7c9b2e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute(sa.text("ALTER TYPE role_enum ADD VALUE IF NOT EXISTS 'iq_user'"))


def downgrade() -> None:
    op.execute(sa.text("UPDATE users SET role = 'learner' WHERE role = 'iq_user'"))
    op.alter_column("users", "role", server_default=None)

    op.execute(sa.text("ALTER TYPE role_enum RENAME TO role_enum_old"))
    op.execute(
        sa.text(
            "CREATE TYPE role_enum AS ENUM ('learner', 'instructor', 'creator', 'org_admin', 'admin', 'psychologist', 'psychologist_pending')"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE users ALTER COLUMN role TYPE role_enum USING role::text::role_enum"
        )
    )
    op.execute(sa.text("DROP TYPE role_enum_old"))
    op.alter_column("users", "role", server_default="learner")