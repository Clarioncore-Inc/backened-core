"""expand lesson content blocks

Revision ID: c31b8a1d2f44
Revises: 587d048fe671
Create Date: 2026-04-15 13:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "c31b8a1d2f44"
down_revision: Union[str, Sequence[str], None] = "587d048fe671"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_type WHERE typname = 'callout_type_enum'
            ) THEN
                CREATE TYPE callout_type_enum AS ENUM ('info', 'warning', 'danger', 'success');
            END IF;
        END
        $$;
        """
    )

    op.execute("ALTER TABLE video_lessons DROP CONSTRAINT IF EXISTS video_lessons_lesson_id_key")
    op.execute("ALTER TABLE text_lessons DROP CONSTRAINT IF EXISTS text_lessons_lesson_id_key")
    op.execute("ALTER TABLE quiz_lessons DROP CONSTRAINT IF EXISTS quiz_lessons_lesson_id_key")
    op.execute("ALTER TABLE interactive_lessons DROP CONSTRAINT IF EXISTS interactive_lessons_lesson_id_key")
    op.execute("ALTER TABLE problem_lessons DROP CONSTRAINT IF EXISTS problem_lessons_lesson_id_key")

    op.execute("ALTER TYPE lesson_kind_enum RENAME TO lesson_kind_enum_old")
    postgresql.ENUM(
        "video", "text", "quiz", "interactive", "problem",
        "heading", "image", "code", "hint", "callout",
        name="lesson_kind_enum",
    ).create(op.get_bind())
    op.execute(
        """
        ALTER TABLE lessons
        ALTER COLUMN kind TYPE lesson_kind_enum
        USING (
            CASE
                WHEN kind::text = 'article' THEN 'text'
                WHEN kind::text = 'practice' THEN 'problem'
                ELSE kind::text
            END
        )::lesson_kind_enum
        """
    )
    op.execute("DROP TYPE lesson_kind_enum_old")

    op.create_table(
        "heading_lessons",
        sa.Column("lesson_id", sa.UUID(), nullable=False),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("level", sa.Integer(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["lesson_id"], ["lessons.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "image_lessons",
        sa.Column("lesson_id", sa.UUID(), nullable=False),
        sa.Column("image_id", sa.UUID(), nullable=False),
        sa.Column("caption", sa.String(), nullable=True),
        sa.Column("alt_text", sa.String(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["image_id"], ["attachments.id"]),
        sa.ForeignKeyConstraint(["lesson_id"], ["lessons.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "code_lessons",
        sa.Column("lesson_id", sa.UUID(), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("language", sa.String(), nullable=True),
        sa.Column("filename", sa.String(), nullable=True),
        sa.Column("show_line_numbers", sa.Boolean(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["lesson_id"], ["lessons.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "hint_lessons",
        sa.Column("lesson_id", sa.UUID(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("is_collapsible", sa.Boolean(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["lesson_id"], ["lessons.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "callout_lessons",
        sa.Column("lesson_id", sa.UUID(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column(
            "callout_type",
            postgresql.ENUM("info", "warning", "danger", "success", name="callout_type_enum", create_type=False),
            nullable=True,
        ),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["lesson_id"], ["lessons.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("callout_lessons")
    op.drop_table("hint_lessons")
    op.drop_table("code_lessons")
    op.drop_table("image_lessons")
    op.drop_table("heading_lessons")

    op.execute("ALTER TYPE lesson_kind_enum RENAME TO lesson_kind_enum_new")
    postgresql.ENUM(
        "video", "interactive", "article", "quiz", "practice",
        name="lesson_kind_enum",
    ).create(op.get_bind())
    op.execute(
        """
        ALTER TABLE lessons
        ALTER COLUMN kind TYPE lesson_kind_enum
        USING (
            CASE
                WHEN kind::text = 'text' THEN 'article'
                WHEN kind::text = 'problem' THEN 'practice'
                WHEN kind::text IN ('heading', 'image', 'code', 'hint', 'callout') THEN 'article'
                ELSE kind::text
            END
        )::lesson_kind_enum
        """
    )
    op.execute("DROP TYPE lesson_kind_enum_new")

    op.create_unique_constraint("video_lessons_lesson_id_key", "video_lessons", ["lesson_id"])
    op.create_unique_constraint("text_lessons_lesson_id_key", "text_lessons", ["lesson_id"])
    op.create_unique_constraint("quiz_lessons_lesson_id_key", "quiz_lessons", ["lesson_id"])
    op.create_unique_constraint("interactive_lessons_lesson_id_key", "interactive_lessons", ["lesson_id"])
    op.create_unique_constraint("problem_lessons_lesson_id_key", "problem_lessons", ["lesson_id"])

    op.execute("DROP TYPE IF EXISTS callout_type_enum")
