"""flashcard mastery and completed-set sessions

Revision ID: 0006_flashcard_mastery
Revises: 0005_curated_flashcards

The migration intentionally requires an empty Flashcard domain. Run the reviewed
``python -m app.flashcard_reset`` workflow before upgrading an existing AKURU
database. Textbook, retrieval, identity and unrelated learner records are not
part of that reset.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0006_flashcard_mastery"
down_revision: Union[str, None] = "0005_curated_flashcards"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _require_empty_flashcards() -> None:
    connection = op.get_bind()
    tables = ("flashcard_reviews", "flashcard_learning_states", "flashcard_sessions",
              "flashcard_versions", "flashcard_decks")
    counts = {table: connection.execute(sa.text(f"SELECT count(*) FROM {table}")).scalar_one()
              for table in tables}
    populated = {table: count for table, count in counts.items() if count}
    if populated:
        detail = ", ".join(f"{table}={count}" for table, count in populated.items())
        raise RuntimeError(
            "Flashcard mastery migration requires the reviewed Flashcard reset first: " + detail
        )


def upgrade() -> None:
    _require_empty_flashcards()

    op.drop_constraint("ck_flashcard_difficulty", "flashcard_versions", type_="check")
    op.alter_column("flashcard_versions", "difficulty", server_default="easy")
    op.create_check_constraint(
        "ck_flashcard_difficulty", "flashcard_versions",
        "difficulty IN ('easy','difficult')",
    )

    op.drop_constraint("ck_flashcard_session_mode", "flashcard_sessions", type_="check")
    op.drop_constraint("ck_flashcard_session_status", "flashcard_sessions", type_="check")
    op.alter_column("flashcard_sessions", "scheduler_version", new_column_name="mastery_version",
                    server_default="akuru-flashcard-mastery-v1")
    op.alter_column("flashcard_sessions", "mode", server_default="review")
    op.add_column("flashcard_sessions", sa.Column(
        "selection_version", sa.String(40), server_default="akuru-flashcard-selection-v2", nullable=False))
    op.add_column("flashcard_sessions", sa.Column("difficulty_filter", sa.String(16), nullable=True))
    op.add_column("flashcard_sessions", sa.Column(
        "revealed_card_version_ids", sa.JSON(), server_default="[]", nullable=False))
    op.create_check_constraint("ck_flashcard_session_mode", "flashcard_sessions",
                               "mode IN ('review','difficult')")
    op.create_check_constraint("ck_flashcard_session_status", "flashcard_sessions",
                               "status IN ('active','completed','discarded')")
    op.create_check_constraint("ck_flashcard_session_difficulty", "flashcard_sessions",
                               "difficulty_filter IS NULL OR difficulty_filter IN ('easy','difficult','mixed')")
    op.create_check_constraint("ck_flashcard_session_target_size", "flashcard_sessions",
                               "target_count BETWEEN 1 AND 30")

    op.drop_constraint("ck_flashcard_review_interval", "flashcard_reviews", type_="check")
    op.drop_index("ix_flashcard_reviews_due_at", table_name="flashcard_reviews")
    op.drop_column("flashcard_reviews", "interval_days")
    op.drop_column("flashcard_reviews", "due_at")
    op.add_column("flashcard_reviews", sa.Column("committed_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_flashcard_reviews_committed_at", "flashcard_reviews", ["committed_at"])

    op.drop_constraint("ck_flashcard_learning_counts", "flashcard_learning_states", type_="check")
    op.drop_constraint("ck_flashcard_learning_ease", "flashcard_learning_states", type_="check")
    op.drop_index("ix_flashcard_learning_states_due_at", table_name="flashcard_learning_states")
    for column in ("repetitions", "lapses", "interval_days", "ease_factor", "due_at"):
        op.drop_column("flashcard_learning_states", column)
    op.add_column("flashcard_learning_states", sa.Column("mastery_score", sa.Float(), server_default="0", nullable=False))
    op.add_column("flashcard_learning_states", sa.Column("mastery_status", sa.String(20), server_default="to_evaluate", nullable=False))
    op.add_column("flashcard_learning_states", sa.Column("consecutive_easy", sa.Integer(), server_default="0", nullable=False))
    op.add_column("flashcard_learning_states", sa.Column("evaluated_count", sa.Integer(), server_default="0", nullable=False))
    op.add_column("flashcard_learning_states", sa.Column(
        "mastery_version", sa.String(40), server_default="akuru-flashcard-mastery-v1", nullable=False))
    op.create_index("ix_flashcard_learning_states_mastery_status", "flashcard_learning_states", ["mastery_status"])
    op.create_check_constraint("ck_flashcard_mastery_score", "flashcard_learning_states",
                               "mastery_score BETWEEN 0 AND 1")
    op.create_check_constraint("ck_flashcard_mastery_counts", "flashcard_learning_states",
                               "consecutive_easy >= 0 AND evaluated_count >= 0")
    op.create_check_constraint("ck_flashcard_mastery_status", "flashcard_learning_states",
                               "mastery_status IN ('to_evaluate','needs_review','good','mastered')")


def downgrade() -> None:
    _require_empty_flashcards()

    op.drop_constraint("ck_flashcard_mastery_status", "flashcard_learning_states", type_="check")
    op.drop_constraint("ck_flashcard_mastery_counts", "flashcard_learning_states", type_="check")
    op.drop_constraint("ck_flashcard_mastery_score", "flashcard_learning_states", type_="check")
    op.drop_index("ix_flashcard_learning_states_mastery_status", table_name="flashcard_learning_states")
    for column in ("mastery_version", "evaluated_count", "consecutive_easy", "mastery_status", "mastery_score"):
        op.drop_column("flashcard_learning_states", column)
    op.add_column("flashcard_learning_states", sa.Column("repetitions", sa.Integer(), server_default="0", nullable=False))
    op.add_column("flashcard_learning_states", sa.Column("lapses", sa.Integer(), server_default="0", nullable=False))
    op.add_column("flashcard_learning_states", sa.Column("interval_days", sa.Integer(), server_default="0", nullable=False))
    op.add_column("flashcard_learning_states", sa.Column("ease_factor", sa.Float(), server_default="2.5", nullable=False))
    op.add_column("flashcard_learning_states", sa.Column("due_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    op.create_index("ix_flashcard_learning_states_due_at", "flashcard_learning_states", ["due_at"])
    op.create_check_constraint("ck_flashcard_learning_counts", "flashcard_learning_states",
                               "repetitions >= 0 AND lapses >= 0 AND interval_days >= 0")
    op.create_check_constraint("ck_flashcard_learning_ease", "flashcard_learning_states",
                               "ease_factor BETWEEN 1.3 AND 3.0")

    op.drop_index("ix_flashcard_reviews_committed_at", table_name="flashcard_reviews")
    op.drop_column("flashcard_reviews", "committed_at")
    op.add_column("flashcard_reviews", sa.Column("interval_days", sa.Integer(), nullable=False))
    op.add_column("flashcard_reviews", sa.Column("due_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_flashcard_reviews_due_at", "flashcard_reviews", ["due_at"])
    op.create_check_constraint("ck_flashcard_review_interval", "flashcard_reviews", "interval_days >= 0")

    op.drop_constraint("ck_flashcard_session_target_size", "flashcard_sessions", type_="check")
    op.drop_constraint("ck_flashcard_session_difficulty", "flashcard_sessions", type_="check")
    op.drop_constraint("ck_flashcard_session_status", "flashcard_sessions", type_="check")
    op.drop_constraint("ck_flashcard_session_mode", "flashcard_sessions", type_="check")
    for column in ("revealed_card_version_ids", "difficulty_filter", "selection_version"):
        op.drop_column("flashcard_sessions", column)
    op.alter_column("flashcard_sessions", "mastery_version", new_column_name="scheduler_version",
                    server_default="akuru-sm2-v1")
    op.alter_column("flashcard_sessions", "mode", server_default="full_topic")
    op.create_check_constraint("ck_flashcard_session_status", "flashcard_sessions",
                               "status IN ('active','completed','abandoned')")
    op.create_check_constraint("ck_flashcard_session_mode", "flashcard_sessions",
                               "mode IN ('quick','normal','full_topic','difficult','due_today','unit_mixed')")

    op.drop_constraint("ck_flashcard_difficulty", "flashcard_versions", type_="check")
    op.alter_column("flashcard_versions", "difficulty", server_default="core")
    op.create_check_constraint("ck_flashcard_difficulty", "flashcard_versions",
                               "difficulty IN ('foundation','core','stretch')")
