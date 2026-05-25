"""make bookmarks polymorphic

Revision ID: 3a7f91c2d4e5
Revises: 1c04e1261ba7
Create Date: 2026-05-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '3a7f91c2d4e5'
down_revision: Union[str, Sequence[str], None] = '1c04e1261ba7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


bookmark_object_type_enum = postgresql.ENUM(
    'lesson',
    'course',
    name='bookmark_object_type_enum',
    create_type=False,
)


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    bookmark_object_type_enum.create(bind, checkfirst=True)

    op.add_column('lesson_bookmarks', sa.Column('object_id', sa.UUID(), nullable=True))
    op.add_column(
        'lesson_bookmarks',
        sa.Column(
            'object_type',
            bookmark_object_type_enum,
            nullable=True,
            server_default=sa.text("'lesson'::bookmark_object_type_enum"),
        ),
    )

    op.execute(
        "UPDATE lesson_bookmarks SET object_id = lesson_id, object_type = 'lesson' "
        "WHERE object_id IS NULL"
    )

    op.alter_column('lesson_bookmarks', 'object_id', nullable=False)
    op.alter_column('lesson_bookmarks', 'object_type', nullable=False, server_default=None)
    op.create_unique_constraint(
        'uq_lesson_bookmarks_user_object',
        'lesson_bookmarks',
        ['user_id', 'object_id', 'object_type'],
    )

    op.execute('ALTER TABLE lesson_bookmarks DROP CONSTRAINT IF EXISTS lesson_bookmarks_lesson_id_fkey')
    op.drop_column('lesson_bookmarks', 'lesson_id')


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()

    op.add_column('lesson_bookmarks', sa.Column('lesson_id', sa.UUID(), nullable=True))
    op.execute("DELETE FROM lesson_bookmarks WHERE object_type = 'course'")
    op.execute("UPDATE lesson_bookmarks SET lesson_id = object_id WHERE object_type = 'lesson'")
    op.alter_column('lesson_bookmarks', 'lesson_id', nullable=False)
    op.create_foreign_key(
        'lesson_bookmarks_lesson_id_fkey',
        'lesson_bookmarks',
        'lessons',
        ['lesson_id'],
        ['id'],
    )

    op.drop_constraint('uq_lesson_bookmarks_user_object', 'lesson_bookmarks', type_='unique')
    op.drop_column('lesson_bookmarks', 'object_type')
    op.drop_column('lesson_bookmarks', 'object_id')
    bookmark_object_type_enum.drop(bind, checkfirst=True)