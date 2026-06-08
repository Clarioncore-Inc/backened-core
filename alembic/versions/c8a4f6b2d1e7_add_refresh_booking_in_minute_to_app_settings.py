"""add refresh booking in minute to app settings

Revision ID: c8a4f6b2d1e7
Revises: f5a1c3d9b2e4
Create Date: 2026-06-08 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c8a4f6b2d1e7"
down_revision: Union[str, Sequence[str], None] = "f5a1c3d9b2e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "app_settings",
        sa.Column(
            "refresh_booking_in_minute",
            sa.Integer(),
            nullable=False,
            server_default="5",
        ),
    )


def downgrade() -> None:
    op.drop_column("app_settings", "refresh_booking_in_minute")