import uuid

import pytest
from fastapi import HTTPException

from app.models import AuthSession, User
from app.permissions import require_student_submission_owner
from app.security import Principal


def principal(role: str, user_id: uuid.UUID) -> Principal:
    return Principal(
        user=User(
            id=user_id,
            username=f"{role}-user",
            display_name="Test User",
            role=role,
            password_hash="unused",
        ),
        session=AuthSession(user_id=user_id, token_hash="token", csrf_hash="csrf"),
    )


def test_student_submission_scope_accepts_only_the_authenticated_student() -> None:
    student_id = uuid.uuid4()
    require_student_submission_owner(principal("student", student_id), student_id)

    with pytest.raises(HTTPException, match="own account") as another_student:
        require_student_submission_owner(principal("student", uuid.uuid4()), student_id)
    assert another_student.value.status_code == 403

    with pytest.raises(HTTPException) as parent:
        require_student_submission_owner(principal("parent", uuid.uuid4()), student_id)
    assert parent.value.status_code == 403
