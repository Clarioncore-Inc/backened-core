"""add pending status and rejection reason to bookings

Revision ID: f2a6c3b7d9e1
Revises: c6b9d0ef4a21
Create Date: 2026-05-09 00:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2a6c3b7d9e1'
down_revision: Union[str, Sequence[str], None] = 'c6b9d0ef4a21'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute(
            sa.text(
                "ALTER TYPE booking_status_enum ADD VALUE IF NOT EXISTS 'pending' BEFORE 'confirmed'"
            )
        )
    op.alter_column('bookings', 'status', server_default='pending')
    op.add_column('bookings', sa.Column('rejection_reason', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('bookings', 'rejection_reason')
    op.alter_column('bookings', 'status', server_default='confirmed')

    op.execute(sa.text("UPDATE bookings SET status = 'confirmed' WHERE status = 'pending'"))
    op.execute(sa.text("ALTER TYPE booking_status_enum RENAME TO booking_status_enum_old"))
    op.execute(
        sa.text(
            "CREATE TYPE booking_status_enum AS ENUM ('confirmed', 'emergency', 'cancelled', 'completed')"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE bookings ALTER COLUMN status TYPE booking_status_enum USING status::text::booking_status_enum"
        )
    )
    op.execute(sa.text("DROP TYPE booking_status_enum_old"))
