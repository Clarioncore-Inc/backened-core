"""add IQ booking test type and certificate id

Revision ID: f9b2c7d4a1e6
Revises: 9f2c7a1d4b6e
Create Date: 2026-06-20 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f9b2c7d4a1e6"
down_revision: Union[str, Sequence[str], None] = "9f2c7a1d4b6e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("bookings", sa.Column("test_type", sa.String(), nullable=True))
    op.add_column("bookings", sa.Column("certificate_id", sa.String(), nullable=True))
    op.create_index(
        "ix_bookings_certificate_id",
        "bookings",
        ["certificate_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_bookings_certificate_id", table_name="bookings")
    op.drop_column("bookings", "certificate_id")
    op.drop_column("bookings", "test_type")
