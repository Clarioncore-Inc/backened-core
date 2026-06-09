"""drop unused psychologist profile fields

Revision ID: e4a7b9c2d3f1
Revises: c8a4f6b2d1e7
Create Date: 2026-06-09 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e4a7b9c2d3f1"
down_revision: Union[str, Sequence[str], None] = "c8a4f6b2d1e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("psychologist_profiles", "allow_emergency_bookings")
    op.drop_column("psychologist_profiles", "is_approved")


def downgrade() -> None:
    op.add_column(
        "psychologist_profiles",
        sa.Column("is_approved", sa.Boolean(), nullable=True, server_default=sa.text("false")),
    )
    op.add_column(
        "psychologist_profiles",
        sa.Column(
            "allow_emergency_bookings",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )