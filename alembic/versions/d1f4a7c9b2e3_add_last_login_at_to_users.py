"""add last login timestamp to users

Revision ID: d1f4a7c9b2e3
Revises: c1f3b9a8d221
Create Date: 2026-06-01 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d1f4a7c9b2e3"
down_revision: Union[str, Sequence[str], None] = "c1f3b9a8d221"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "last_login_at")