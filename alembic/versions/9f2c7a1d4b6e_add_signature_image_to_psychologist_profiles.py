"""add signature image to psychologist profiles

Revision ID: 9f2c7a1d4b6e
Revises: e4a7b9c2d3f1
Create Date: 2026-06-14 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9f2c7a1d4b6e"
down_revision: Union[str, Sequence[str], None] = "e4a7b9c2d3f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "psychologist_profiles",
        sa.Column("signature_image", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("psychologist_profiles", "signature_image")