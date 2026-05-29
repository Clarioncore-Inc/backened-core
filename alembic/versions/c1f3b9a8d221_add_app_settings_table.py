"""add app settings table

Revision ID: c1f3b9a8d221
Revises: 8c2c6f2a1d2b
Create Date: 2026-05-29 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "c1f3b9a8d221"
down_revision: Union[str, Sequence[str], None] = "8c2c6f2a1d2b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "app_settings",
        sa.Column("app_name", sa.String(), nullable=False, server_default="CerebroLearn"),
        sa.Column("logo", sa.String(), nullable=True),
        sa.Column("contacts", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column(
            "iq_test_price",
            sa.Numeric(10, 2),
            nullable=False,
            server_default=sa.text("299.0"),
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("app_settings")