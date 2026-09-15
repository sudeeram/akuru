"""Apply AKURU privacy retention and student-artifact deletion policies."""
from __future__ import annotations

import argparse
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, select, update

from app.config import get_settings
from app.database import SessionLocal
from app.models import (
    Assessment,
    AssessmentAnswer,
    AssessmentResult,
    AssessmentWorkingFile,
    AuditEvent,
    EducationalMedia,
    TutorSession,
    TutorTurn,
)
from app.storage import get_storage


def purge(*, student_id: uuid.UUID | None = None, dry_run: bool = True) -> dict[str, int]:
    settings, storage = get_settings(), get_storage()
    now = datetime.now(timezone.utc)
    counts = {
        "workingFiles": 0,
        "answersRedacted": 0,
        "resultsRedacted": 0,
        "tutorTurnsRedacted": 0,
        "mediaDeleted": 0,
        "auditDeleted": 0,
    }
    with SessionLocal() as db:
        working_query = select(AssessmentWorkingFile)
        if student_id:
            working_query = working_query.where(AssessmentWorkingFile.student_id == student_id)
        else:
            working_query = working_query.where(AssessmentWorkingFile.created_at < now - timedelta(days=settings.working_file_retention_days))
        working = db.scalars(working_query).all(); counts["workingFiles"] = len(working)
        assessment_ids = select(Assessment.id)
        if student_id:
            assessment_ids = assessment_ids.where(Assessment.student_id == student_id)
        else:
            assessment_ids = assessment_ids.where(Assessment.submitted_at < now - timedelta(days=settings.assessment_answer_retention_days))
        answer_rows = db.scalars(select(AssessmentAnswer).where(AssessmentAnswer.assessment_id.in_(assessment_ids))).all()
        result_rows = db.scalars(select(AssessmentResult).where(AssessmentResult.assessment_id.in_(assessment_ids))).all()
        counts["answersRedacted"], counts["resultsRedacted"] = len(answer_rows), len(result_rows)
        tutor_turns = []
        if student_id:
            tutor_session_ids = select(TutorSession.id).where(TutorSession.student_id == student_id)
            tutor_turns = db.scalars(
                select(TutorTurn).where(
                    TutorTurn.session_id.in_(tutor_session_ids),
                    TutorTurn.purged_at.is_(None),
                )
            ).all()
            counts["tutorTurnsRedacted"] = len(tutor_turns)
        media = db.scalars(select(EducationalMedia).where(EducationalMedia.status.in_(("pending_review", "rejected")), EducationalMedia.created_at < now - timedelta(days=settings.rejected_media_retention_days))).all()
        counts["mediaDeleted"] = len(media)
        if student_id is None:
            counts["auditDeleted"] = db.scalar(select(func.count()).select_from(AuditEvent).where(AuditEvent.created_at < now - timedelta(days=settings.audit_retention_days))) or 0
        if dry_run: return counts
        for row in working:
            storage.delete(row.object_key)
            db.execute(update(AssessmentAnswer).where(AssessmentAnswer.file_id == str(row.id)).values(file_id=None))
            db.delete(row)
        for row in answer_rows: row.answer_text, row.file_id = "", None
        for row in result_rows:
            row.marking_decisions = [{**item, "studentEvidence": ""} for item in row.marking_decisions]
            row.pass_one_output, row.pass_two_output = {}, {}
            row.strengths, row.small_mistakes, row.conceptual_mistakes = [], [], []
            row.improved_answer, row.teaching_explanation = "", ""
            row.unit_evidence, row.recommendations = [], []
        for row in tutor_turns:
            row.content = "[Transcript content removed following a child-data deletion request.]"
            row.response_data = {}
            row.purged_at = now
        for row in media:
            storage.delete(row.object_key); db.delete(row)
        if student_id is None:
            db.execute(delete(AuditEvent).where(AuditEvent.created_at < now - timedelta(days=settings.audit_retention_days)))
        db.commit(); return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--student-id", type=uuid.UUID)
    parser.add_argument("--apply", action="store_true", help="Apply deletion; default is a dry run")
    args = parser.parse_args()
    print(purge(student_id=args.student_id, dry_run=not args.apply))

if __name__ == "__main__": main()
