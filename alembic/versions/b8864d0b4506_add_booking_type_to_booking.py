"""add booking type to booking

Revision ID: b8864d0b4506
Revises: aaaaaaaaaaaa
Create Date: 2026-05-06 20:23:45.248733

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b8864d0b4506'
down_revision: Union[str, Sequence[str], None] = 'aaaaaaaaaaaa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    booking_type_enum = postgresql.ENUM(
        'emergency', 'standard', name='booking_type_enum')
    booking_type_enum.create(op.get_bind(), checkfirst=True)

    op.add_column('bookings', sa.Column(
        'booking_type',
        postgresql.ENUM('emergency', 'standard',
                        name='booking_type_enum', create_type=False),
        nullable=True,
        server_default='standard'
    ))


def downgrade() -> None:
    op.drop_column('bookings', 'booking_type')
    postgresql.ENUM(name='booking_type_enum').drop(
        op.get_bind(), checkfirst=True)
