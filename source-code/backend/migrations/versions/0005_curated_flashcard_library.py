"""curated flashcard library and adaptive review

Revision ID: 0005_curated_flashcards
Revises: 0004_topic_visual_assets
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0005_curated_flashcards"
down_revision: Union[str, None] = "0004_topic_visual_assets"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("flashcard_versions", sa.Column("external_key", sa.String(120), server_default="", nullable=False))
    op.add_column("flashcard_versions", sa.Column("concept_key", sa.String(120), server_default="", nullable=False))
    op.add_column("flashcard_versions", sa.Column("category", sa.String(40), server_default="essential_knowledge", nullable=False))
    op.add_column("flashcard_versions", sa.Column("variation_type", sa.String(32), server_default="recall", nullable=False))
    op.add_column("flashcard_versions", sa.Column("difficulty", sa.String(16), server_default="core", nullable=False))
    op.add_column("flashcard_versions", sa.Column("card_metadata", sa.JSON(), server_default="{}", nullable=False))
    op.add_column("flashcard_versions", sa.Column("visual_asset_id", sa.Uuid(), nullable=True))
    op.execute("UPDATE flashcard_versions SET external_key = 'legacy-' || ordinal::text, concept_key = 'legacy-' || ordinal::text")
    op.create_foreign_key("fk_flashcard_visual_asset", "flashcard_versions", "textbook_topic_visual_assets", ["visual_asset_id"], ["id"], ondelete="RESTRICT")
    op.create_index("ix_flashcard_versions_concept_key", "flashcard_versions", ["concept_key"])
    op.create_unique_constraint("uq_flashcard_external_version", "flashcard_versions", ["deck_id", "external_key", "version_number"])
    op.create_check_constraint("ck_flashcard_category", "flashcard_versions", "category IN ('essential_knowledge','explanation_comparison','application_misconception','calculation_interpretation_diagram')")
    op.create_check_constraint("ck_flashcard_variation", "flashcard_versions", "variation_type IN ('recall','explanation','comparison','application','misconception','calculation','interpretation','diagram')")
    op.create_check_constraint("ck_flashcard_difficulty", "flashcard_versions", "difficulty IN ('foundation','core','stretch')")

    op.add_column("flashcard_sessions", sa.Column("mode", sa.String(24), server_default="full_topic", nullable=False))
    op.add_column("flashcard_sessions", sa.Column("target_count", sa.Integer(), server_default="0", nullable=False))
    op.add_column("flashcard_sessions", sa.Column("selected_card_version_ids", sa.JSON(), server_default="[]", nullable=False))
    op.add_column("flashcard_sessions", sa.Column("selection_reasons", sa.JSON(), server_default="[]", nullable=False))
    op.create_index("ix_flashcard_sessions_mode", "flashcard_sessions", ["mode"])
    op.create_check_constraint("ck_flashcard_session_target", "flashcard_sessions", "target_count >= 0")
    op.create_check_constraint("ck_flashcard_session_mode", "flashcard_sessions", "mode IN ('quick','normal','full_topic','difficult','due_today','unit_mixed')")

    op.create_table("flashcard_learning_states",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("card_version_id", sa.Uuid(), nullable=False),
        sa.Column("concept_key", sa.String(120), nullable=False),
        sa.Column("repetitions", sa.Integer(), server_default="0", nullable=False),
        sa.Column("lapses", sa.Integer(), server_default="0", nullable=False),
        sa.Column("interval_days", sa.Integer(), server_default="0", nullable=False),
        sa.Column("ease_factor", sa.Float(), server_default="2.5", nullable=False),
        sa.Column("last_rating", sa.String(16), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("repetitions >= 0 AND lapses >= 0 AND interval_days >= 0", name="ck_flashcard_learning_counts"),
        sa.CheckConstraint("ease_factor BETWEEN 1.3 AND 3.0", name="ck_flashcard_learning_ease"),
        sa.CheckConstraint("last_rating IS NULL OR last_rating IN ('again','difficult','good','easy')", name="ck_flashcard_learning_rating"),
        sa.ForeignKeyConstraint(["card_version_id"], ["flashcard_versions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["student_id"], ["student_profiles.student_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "card_version_id", name="uq_flashcard_learning_student_card"),
    )
    op.create_index("ix_flashcard_learning_states_student_id", "flashcard_learning_states", ["student_id"])
    op.create_index("ix_flashcard_learning_states_card_version_id", "flashcard_learning_states", ["card_version_id"])
    op.create_index("ix_flashcard_learning_states_concept_key", "flashcard_learning_states", ["concept_key"])
    op.create_index("ix_flashcard_learning_states_due_at", "flashcard_learning_states", ["due_at"])


def downgrade() -> None:
    op.drop_table("flashcard_learning_states")
    op.drop_constraint("ck_flashcard_session_mode", "flashcard_sessions", type_="check")
    op.drop_constraint("ck_flashcard_session_target", "flashcard_sessions", type_="check")
    op.drop_index("ix_flashcard_sessions_mode", table_name="flashcard_sessions")
    for column in ("selection_reasons", "selected_card_version_ids", "target_count", "mode"):
        op.drop_column("flashcard_sessions", column)
    op.drop_constraint("ck_flashcard_difficulty", "flashcard_versions", type_="check")
    op.drop_constraint("ck_flashcard_variation", "flashcard_versions", type_="check")
    op.drop_constraint("ck_flashcard_category", "flashcard_versions", type_="check")
    op.drop_constraint("uq_flashcard_external_version", "flashcard_versions", type_="unique")
    op.drop_index("ix_flashcard_versions_concept_key", table_name="flashcard_versions")
    op.drop_constraint("fk_flashcard_visual_asset", "flashcard_versions", type_="foreignkey")
    for column in ("visual_asset_id", "card_metadata", "difficulty", "variation_type", "category", "concept_key", "external_key"):
        op.drop_column("flashcard_versions", column)
