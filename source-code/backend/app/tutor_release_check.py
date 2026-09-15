"""Fail closed when production-like staging lacks complete Tutor release evidence."""
from sqlalchemy import select

from app.database import SessionLocal
from app.models import EvaluationRelease, Subject
from app.services.evaluations import PHASE1_SUBJECTS, TUTOR_RELEASE_MODALITY, tutor_feature_allowed


def main() -> int:
    failures: list[str] = []
    with SessionLocal() as db:
        enabled_subjects = set(db.scalars(select(Subject.id).where(Subject.id.in_(PHASE1_SUBJECTS))).all())
        for subject_id in sorted(enabled_subjects):
            for workflow in TUTOR_RELEASE_MODALITY:
                allowed, reason = tutor_feature_allowed(db, subject_id, workflow)
                if not allowed:
                    failures.append(f"{subject_id}/{workflow}: {reason}")
        releases = db.scalars(select(EvaluationRelease).where(
            EvaluationRelease.workflow.in_(tuple(TUTOR_RELEASE_MODALITY)))).all()
        if not releases:
            failures.append("No Tutor release gates exist.")
    if failures:
        print("Tutor staging release check BLOCKED")
        for failure in failures: print(f"- {failure}")
        return 1
    print("Tutor staging release check PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
