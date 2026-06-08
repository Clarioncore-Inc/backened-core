"""add psychologist booking reminder minutes to app settings

Revision ID: f5a1c3d9b2e4
Revises: e3b1c2d4f5a6
Create Date: 2026-06-08 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f5a1c3d9b2e4"
down_revision: Union[str, Sequence[str], None] = "e3b1c2d4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "app_settings",
        sa.Column(
            "psychologist_booking_reminder_in_minutes",
            sa.Integer(),
            nullable=False,
            server_default="30",
        ),
    )


def downgrade() -> None:
    op.drop_column("app_settings", "psychologist_booking_reminder_in_minutes")