"""Distinguish confidence-based approval from human approval."""
from alembic import op

revision = "0020_question_ai_approval"
down_revision = "0019_tutor_chat_scope"
branch_labels = depends_on = None


def upgrade():
    op.drop_constraint("ck_official_review_question_status", "official_paper_review_questions")
    op.create_check_constraint("ck_official_review_question_status", "official_paper_review_questions",
        "status IN ('unreviewed','needs_correction','ready_for_approval','approved','ai_approved','excluded')")


def downgrade():
    # Never relabel an AI decision as a human approval.
    op.execute("UPDATE official_paper_review_questions SET status = CASE WHEN status = 'ai_approved' THEN 'unreviewed' ELSE status END, "
        "review_data = jsonb_set(review_data::jsonb, '{parts}', COALESCE((SELECT jsonb_agg("
        "CASE WHEN p->>'status' = 'ai_approved' THEN jsonb_set(p, '{status}', '\"unreviewed\"') ELSE p END) "
        "FROM jsonb_array_elements(review_data::jsonb->'parts') p), '[]'::jsonb)) "
        "WHERE status = 'ai_approved' OR review_data::text LIKE '%ai_approved%'")
    op.drop_constraint("ck_official_review_question_status", "official_paper_review_questions")
    op.create_check_constraint("ck_official_review_question_status", "official_paper_review_questions",
        "status IN ('unreviewed','needs_correction','ready_for_approval','approved','excluded')")
