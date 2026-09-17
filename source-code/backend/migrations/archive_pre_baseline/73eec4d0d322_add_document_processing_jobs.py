"""add document processing jobs

Revision ID: 73eec4d0d322
Revises: 521493ec5f1f
Create Date: 2026-09-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "73eec4d0d322"
down_revision: Union[str, None] = "521493ec5f1f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("ck_document_versions_status", "document_versions", type_="check")
    op.create_check_constraint(
        "ck_document_versions_status",
        "document_versions",
        "status IN ('uploaded','queued','processing','needs_review','failed','completed','removed')",
    )
    op.create_table(
        "document_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("document_version_id", sa.Uuid(), nullable=False),
        sa.Column("stage", sa.String(length=40), server_default="preflight", nullable=False),
        sa.Column("status", sa.String(length=24), server_default="queued", nullable=False),
        sa.Column("progress", sa.Integer(), server_default="0", nullable=False),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("extraction_version", sa.String(length=80), nullable=False),
        sa.Column("error_code", sa.String(length=80), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("result_data", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("max_seconds", sa.Integer(), nullable=False),
        sa.Column("max_memory_mb", sa.Integer(), nullable=False),
        sa.Column("max_pages", sa.Integer(), nullable=False),
        sa.Column("queued_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "status IN ('queued','processing','needs_review','failed','completed')",
            name="ck_document_jobs_status",
        ),
        sa.CheckConstraint("progress BETWEEN 0 AND 100", name="ck_document_jobs_progress"),
        sa.CheckConstraint("attempt_count >= 0", name="ck_document_jobs_attempt_count"),
        sa.CheckConstraint("max_seconds > 0", name="ck_document_jobs_max_seconds"),
        sa.CheckConstraint("max_memory_mb > 0", name="ck_document_jobs_max_memory"),
        sa.CheckConstraint("max_pages > 0", name="ck_document_jobs_max_pages"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_version_id"], ["document_versions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "document_version_id", "stage", "extraction_version",
            name="uq_document_job_stage_version",
        ),
    )
    op.create_index(op.f("ix_document_jobs_document_id"), "document_jobs", ["document_id"])
    op.create_index(op.f("ix_document_jobs_document_version_id"), "document_jobs", ["document_version_id"])
    op.create_index(op.f("ix_document_jobs_status"), "document_jobs", ["status"])

    op.create_table(
        "document_stage_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_version_id", sa.Uuid(), nullable=False),
        sa.Column("stage", sa.String(length=40), nullable=False),
        sa.Column("extraction_version", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("input_checksum", sa.String(length=64), nullable=False),
        sa.Column("output_data", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('processing','failed','completed')",
            name="ck_document_stage_runs_status",
        ),
        sa.ForeignKeyConstraint(["document_version_id"], ["document_versions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "document_version_id", "stage", "extraction_version",
            name="uq_document_stage_run_version",
        ),
    )
    op.create_index(
        op.f("ix_document_stage_runs_document_version_id"),
        "document_stage_runs",
        ["document_version_id"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_document_stage_runs_document_version_id"),
        table_name="document_stage_runs",
    )
    op.drop_table("document_stage_runs")
    op.drop_index(op.f("ix_document_jobs_status"), table_name="document_jobs")
    op.drop_index(op.f("ix_document_jobs_document_version_id"), table_name="document_jobs")
    op.drop_index(op.f("ix_document_jobs_document_id"), table_name="document_jobs")
    op.drop_table("document_jobs")
    op.drop_constraint("ck_document_versions_status", "document_versions", type_="check")
    op.create_check_constraint(
        "ck_document_versions_status",
        "document_versions",
        "status IN ('uploaded','failed','removed')",
    )
