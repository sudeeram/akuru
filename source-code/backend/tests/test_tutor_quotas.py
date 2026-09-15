import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.database import engine
from app.errors import DomainError
from app.models import StudentAIQuota, StudentAIUsage, StudentProfile, User
from app.security import hash_password
from app.services import tutor_quotas


@pytest.mark.integration
def test_atomic_quota_reservation_prevents_concurrent_overspend_and_releases_failures() -> None:
    suffix = uuid.uuid4().hex
    parent_id = uuid.uuid4(); student_id = uuid.uuid4()
    with Session(engine) as db:
        db.add_all([
            User(id=parent_id, username=f"quota-parent-{suffix}", display_name="Quota Parent", role="parent",
                 password_hash=hash_password("quota parent test password"), must_change_password=False),
            User(id=student_id, username=f"quota-student-{suffix}", display_name="Quota Student", role="student",
                 password_hash=hash_password("quota student test password"), must_change_password=False),
        ])
        db.flush(); db.add(StudentProfile(student_id=student_id, parent_id=parent_id)); db.flush()
        db.add(StudentAIQuota(student_id=student_id, request_allowance=1, text_token_allowance=1000,
                              voice_seconds_allowance=60)); db.commit()

    barrier = Barrier(2)
    def reserve(operation: str) -> str:
        with Session(engine) as db:
            barrier.wait()
            try:
                tutor_quotas.reserve_text(db, student_id, operation, 100)
                db.commit(); return "reserved"
            except DomainError as error:
                db.rollback(); return error.code

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(reserve, ("parallel-one", "parallel-two")))
        assert sorted(results) == ["reserved", "student_ai_request_quota_exhausted"]
        with Session(engine) as db:
            reserved = db.scalars(select(StudentAIUsage).where(StudentAIUsage.student_id == student_id)).all()
            operation = next(row.operation_id for row in reserved if row.dimension == "request")
            tutor_quotas.release_text(db, student_id, operation, 100, "provider_failed")
            tutor_quotas.release_text(db, student_id, operation, 100, "provider_failed")
            db.commit()
            totals = {dimension: sum(row.quantity for row in db.scalars(select(StudentAIUsage).where(
                StudentAIUsage.student_id == student_id, StudentAIUsage.dimension == dimension)).all())
                for dimension in ("request", "text_token")}
            assert totals == {"request": 0, "text_token": 0}
    finally:
        with Session(engine) as db:
            db.execute(delete(User).where(User.id == student_id)); db.execute(delete(User).where(User.id == parent_id)); db.commit()
