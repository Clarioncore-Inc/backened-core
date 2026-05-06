"""add status to psycology register

Revision ID: 5e7a6b99e600
Revises: 88274a691abb
Create Date: 2026-05-06 10:50:14.304961

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '5e7a6b99e600'
down_revision: Union[str, Sequence[str], None] = '88274a691abb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    psychologist_profile_enum = postgresql.ENUM(
        'pending', 'approved', 'rejected',
        name='psychologist_profile_enum',
        create_type=True
    )
    psychologist_profile_enum.create(op.get_bind(), checkfirst=True)

    op.add_column('psychologist_profiles', sa.Column(
        'psychologist_status',
        postgresql.ENUM('pending', 'approved', 'rejected',
                        name='psychologist_profile_enum', create_type=False),
        nullable=True
    ))
    op.drop_column('psychologist_profiles', 'status')


def downgrade() -> None:
    op.add_column('psychologist_profiles', sa.Column(
        'status',
        postgresql.ENUM('pending', 'approved', 'rejected',
                        name='profile_status_enum', create_type=False),
        server_default=sa.text("'pending'::profile_status_enum"),
        autoincrement=False,
        nullable=True
    ))
    op.drop_column('psychologist_profiles', 'psychologist_status')

    postgresql.ENUM(name='psychologist_profile_enum').drop(
        op.get_bind(), checkfirst=True)


"""add status to psycology register

Revision ID: 5e7a6b99e600
Revises: 88274a691abb
Create Date: 2026-05-06 10:50:14.304961

"""

revision: str = '5e7a6b99e600'
down_revision: Union[str, Sequence[str], None] = '88274a691abb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
