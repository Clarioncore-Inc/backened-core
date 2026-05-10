"""add psychologist settings and booking notes

Revision ID: c6b9d0ef4a21
Revises: 47c2dcd284c8
Create Date: 2026-05-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c6b9d0ef4a21'
down_revision: Union[str, Sequence[str], None] = '47c2dcd284c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    booking_type_enum = postgresql.ENUM(
        'emergency',
        'standard',
        name='booking_type_enum',
        create_type=False,
    )
    booking_type_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        'psychologist_profiles',
        sa.Column('default_session_duration', sa.Integer(), nullable=True, server_default='60'),
    )
    op.add_column(
        'psychologist_profiles',
        sa.Column('default_booking_type', booking_type_enum, nullable=True, server_default='standard'),
    )
    op.add_column(
        'psychologist_profiles',
        sa.Column('allow_emergency_bookings', sa.Boolean(), nullable=False, server_default=sa.text('false')),
    )
    op.add_column(
        'psychologist_profiles',
        sa.Column('is_profile_public', sa.Boolean(), nullable=False, server_default=sa.text('true')),
    )
    op.add_column(
        'psychologist_profiles',
        sa.Column('accepting_new_clients', sa.Boolean(), nullable=False, server_default=sa.text('true')),
    )
    op.add_column(
        'psychologist_profiles',
        sa.Column(
            'visible_profile_fields',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{\"bio\": true, \"location\": true, \"phone_number\": false, \"hourly_rate\": true}'::jsonb"),
        ),
    )

    op.add_column(
        'bookings',
        sa.Column('session_notes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        'bookings',
        sa.Column('session_notes_updated_at', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('bookings', 'session_notes_updated_at')
    op.drop_column('bookings', 'session_notes')

    op.drop_column('psychologist_profiles', 'visible_profile_fields')
    op.drop_column('psychologist_profiles', 'accepting_new_clients')
    op.drop_column('psychologist_profiles', 'is_profile_public')
    op.drop_column('psychologist_profiles', 'allow_emergency_bookings')
    op.drop_column('psychologist_profiles', 'default_booking_type')
    op.drop_column('psychologist_profiles', 'default_session_duration')