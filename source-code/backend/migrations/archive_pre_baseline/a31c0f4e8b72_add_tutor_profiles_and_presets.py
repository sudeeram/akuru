"""add tutor profiles and curated presets

Revision ID: a31c0f4e8b72
Revises: f20c81d45a02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a31c0f4e8b72"
down_revision: Union[str, None] = "f20c81d45a02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "tutor_avatars",
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("display_name", sa.String(80), nullable=False),
        sa.Column("description", sa.String(240), nullable=False),
        sa.Column("image_path", sa.String(240), nullable=False),
        sa.Column("presentation", sa.String(16), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("presentation IN ('masculine','feminine','neutral')", name="ck_tutor_avatar_presentation"),
        sa.CheckConstraint("sort_order BETWEEN 0 AND 1000", name="ck_tutor_avatar_sort_order"),
        sa.PrimaryKeyConstraint("code"),
    )
    op.create_table(
        "tutor_voice_presets",
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("display_name", sa.String(80), nullable=False),
        sa.Column("description", sa.String(240), nullable=False),
        sa.Column("provider_voice_ref", sa.String(80), nullable=True),
        sa.Column("presentation", sa.String(16), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("presentation IN ('masculine','feminine','neutral')", name="ck_tutor_voice_presentation"),
        sa.CheckConstraint("sort_order BETWEEN 0 AND 1000", name="ck_tutor_voice_sort_order"),
        sa.PrimaryKeyConstraint("code"),
    )
    op.create_table(
        "tutor_profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("public_ref", sa.String(48), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("current_version_number", sa.Integer(), server_default="1", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("current_version_number > 0", name="ck_tutor_profile_current_version"),
        sa.ForeignKeyConstraint(["student_id"], ["student_profiles.student_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tutor_profiles_public_ref", "tutor_profiles", ["public_ref"], unique=True)
    op.create_index("ix_tutor_profiles_student_id", "tutor_profiles", ["student_id"])
    op.create_table(
        "tutor_profile_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(60), nullable=False),
        sa.Column("presentation", sa.String(16), nullable=False),
        sa.Column("avatar_code", sa.String(40), nullable=False),
        sa.Column("voice_code", sa.String(40), nullable=False),
        sa.Column("tone", sa.String(16), nullable=False),
        sa.Column("friendliness", sa.String(8), nullable=False),
        sa.Column("enthusiasm", sa.String(8), nullable=False),
        sa.Column("speed", sa.String(8), nullable=False),
        sa.Column("communication_character", sa.String(16), nullable=False),
        sa.Column("explanation_depth", sa.String(16), nullable=False),
        sa.Column("teaching_style", sa.String(20), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("version_number > 0", name="ck_tutor_profile_version_number"),
        sa.CheckConstraint("presentation IN ('masculine','feminine','neutral')", name="ck_tutor_profile_presentation"),
        sa.CheckConstraint("tone IN ('calm','encouraging','direct','playful')", name="ck_tutor_profile_tone"),
        sa.CheckConstraint("friendliness IN ('low','medium','high')", name="ck_tutor_profile_friendliness"),
        sa.CheckConstraint("enthusiasm IN ('low','medium','high')", name="ck_tutor_profile_enthusiasm"),
        sa.CheckConstraint("speed IN ('low','medium','high')", name="ck_tutor_profile_speed"),
        sa.CheckConstraint("communication_character IN ('childlike','balanced','authoritative')", name="ck_tutor_profile_character"),
        sa.CheckConstraint("explanation_depth IN ('concise','standard','detailed')", name="ck_tutor_profile_depth"),
        sa.CheckConstraint("teaching_style IN ('guided','socratic','example_led','exam_focused')", name="ck_tutor_profile_teaching_style"),
        sa.ForeignKeyConstraint(["avatar_code"], ["tutor_avatars.code"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["profile_id"], ["tutor_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["voice_code"], ["tutor_voice_presets.code"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("profile_id", "version_number", name="uq_tutor_profile_version"),
    )
    op.create_index("ix_tutor_profile_versions_profile_id", "tutor_profile_versions", ["profile_id"])

    avatars = sa.table(
        "tutor_avatars",
        sa.column("code", sa.String), sa.column("display_name", sa.String),
        sa.column("description", sa.String), sa.column("image_path", sa.String),
        sa.column("presentation", sa.String), sa.column("is_enabled", sa.Boolean),
        sa.column("sort_order", sa.Integer),
    )
    op.bulk_insert(avatars, [
        {"code": "akuru-atlas", "display_name": "Atlas", "description": "A confident idea hero for structured challenges.", "image_path": "/akuru-bots/akuru-bot-idea.png", "presentation": "masculine", "is_enabled": True, "sort_order": 10},
        {"code": "akuru-nova", "display_name": "Nova", "description": "A thoughtful reading hero who explains with care.", "image_path": "/akuru-bots/akuru-bot-reader.png", "presentation": "feminine", "is_enabled": True, "sort_order": 20},
        {"code": "akuru-spark", "display_name": "Spark", "description": "An upbeat learning hero who celebrates progress.", "image_path": "/akuru-bots/akuru-bot-celebrate.png", "presentation": "neutral", "is_enabled": True, "sort_order": 30},
        {"code": "akuru-orbit", "display_name": "Orbit", "description": "A curious hero for questions and discoveries.", "image_path": "/akuru-bots/akuru-bot-curious.png", "presentation": "neutral", "is_enabled": True, "sort_order": 40},
        {"code": "akuru-byte", "display_name": "Byte", "description": "A focused technology hero for worked examples.", "image_path": "/akuru-bots/akuru-bot-laptop.png", "presentation": "masculine", "is_enabled": True, "sort_order": 50},
    ])
    voices = sa.table(
        "tutor_voice_presets",
        sa.column("code", sa.String), sa.column("display_name", sa.String),
        sa.column("description", sa.String), sa.column("provider_voice_ref", sa.String),
        sa.column("presentation", sa.String), sa.column("is_enabled", sa.Boolean),
        sa.column("sort_order", sa.Integer),
    )
    op.bulk_insert(voices, [
        {"code": "clear-coach", "display_name": "Clear coach", "description": "A clear, steady masculine presentation.", "provider_voice_ref": None, "presentation": "masculine", "is_enabled": True, "sort_order": 10},
        {"code": "warm-guide", "display_name": "Warm guide", "description": "A warm, patient feminine presentation.", "provider_voice_ref": None, "presentation": "feminine", "is_enabled": True, "sort_order": 20},
        {"code": "bright-companion", "display_name": "Bright companion", "description": "A lively neutral presentation.", "provider_voice_ref": None, "presentation": "neutral", "is_enabled": True, "sort_order": 30},
    ])


def downgrade():
    op.drop_table("tutor_profile_versions")
    op.drop_index("ix_tutor_profiles_student_id", table_name="tutor_profiles")
    op.drop_index("ix_tutor_profiles_public_ref", table_name="tutor_profiles")
    op.drop_table("tutor_profiles")
    op.drop_table("tutor_voice_presets")
    op.drop_table("tutor_avatars")
