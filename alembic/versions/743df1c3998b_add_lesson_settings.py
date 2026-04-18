"""Add Lesson settings

Revision ID: 743df1c3998b
Revises: db198a9c37d0
Create Date: 2026-04-18 15:38:53.217380

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '743df1c3998b'
down_revision: Union[str, Sequence[str], None] = 'db198a9c37d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create enum types first
    op.execute("CREATE TYPE parent_type_enum AS ENUM ('lesson','video_lesson','text_lesson','quiz_lesson','interactive_lesson','problem_lesson','heading_lesson','image_lesson','code_lesson','hint_lesson','callout_lesson')")
    op.execute(
        "CREATE TYPE difficultyenum AS ENUM ('BEGINNER','INTERMEDIATE','ADVANCED')")

    # Add nesting columns to all content tables
    for table in ["video_lessons", "text_lessons", "quiz_lessons", "interactive_lessons",
                  "problem_lessons", "heading_lessons", "image_lessons", "code_lessons",
                  "hint_lessons", "callout_lessons"]:
        op.add_column(table, sa.Column('parent_id', sa.UUID(), nullable=True))
        op.add_column(table, sa.Column('parent_type', postgresql.ENUM('lesson', 'video_lesson', 'text_lesson', 'quiz_lesson', 'interactive_lesson',
                      'problem_lesson', 'heading_lesson', 'image_lesson', 'code_lesson', 'hint_lesson', 'callout_lesson', name='parent_type_enum'), nullable=True))
        op.add_column(table, sa.Column(
            'position', sa.Integer(), nullable=True))

    # Add lesson settings only to lessons table
    op.add_column('lessons', sa.Column(
        'xp_reward', sa.Integer(), nullable=True))
    op.add_column('lessons', sa.Column('difficulty', postgresql.ENUM(
        'BEGINNER', 'INTERMEDIATE', 'ADVANCED', name='difficultyenum'), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove lesson settings from lessons table
    op.drop_column('lessons', 'difficulty')
    op.drop_column('lessons', 'xp_reward')

    # Remove nesting columns from all content tables
    for table in ["video_lessons", "text_lessons", "quiz_lessons", "interactive_lessons",
                  "problem_lessons", "heading_lessons", "image_lessons", "code_lessons",
                  "hint_lessons", "callout_lessons"]:
        op.drop_column(table, 'position')
        op.drop_column(table, 'parent_type')
        op.drop_column(table, 'parent_id')

    # Drop the enum types
    op.execute("DROP TYPE IF EXISTS difficultyenum")
    op.execute("DROP TYPE IF EXISTS parent_type_enum")
