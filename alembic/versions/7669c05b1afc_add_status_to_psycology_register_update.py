"""add status to psycology register update

Revision ID: 7669c05b1afc
Revises: 5e7a6b99e600
Create Date: 2026-05-06 11:04:49.114503

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '7669c05b1afc'
down_revision: Union[str, Sequence[str], None] = '5e7a6b99e600'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    postgresql.ENUM('pending', 'approved', 'rejected', name='psychologist_profile_enum').create(op.get_bind(), checkfirst=True)
    op.add_column('psychologist_profiles', sa.Column(
        'status',
        postgresql.ENUM('pending', 'approved', 'rejected', name='psychologist_profile_enum', create_type=False),
        nullable=True,
        server_default='pending'
    ))

def downgrade() -> None:
    op.drop_column('psychologist_profiles', 'status')
    postgresql.ENUM(name='psychologist_profile_enum').drop(op.get_bind(), checkfirst=True)
