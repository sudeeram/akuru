from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import DomainError
from app.models import AuditEvent, StudentProfile, User
from app.repositories.catalog import CatalogRepository
from app.repositories.students import StudentRepository
from app.repositories.users import UserRepository
from app.schemas.accounts import AccountResponse, CreateAccountRequest, UpdateStudentRequest
from app.security import Principal, hash_password


def parse_progression(payload: CreateAccountRequest | UpdateStudentRequest) -> list[tuple[int, int]]:
    if isinstance(payload, CreateAccountRequest) and payload.role != "student":
        return []
    parsed: set[tuple[int, int]] = set()
    for value in payload.progression:
        try:
            grade_name, term_name = value.split("|", 1)
            parsed.add((int(grade_name.removeprefix("Grade ")), int(term_name.removeprefix("Term"))))
        except (ValueError, AttributeError) as exc:
            raise DomainError("invalid_progression", "Choose valid Grade and Term combinations.", 422) from exc
    if any(grade not in (10, 11) or term not in (1, 2, 3) for grade, term in parsed):
        raise DomainError("invalid_progression", "Choose valid Grade and Term combinations.", 422)
    ordered = sorted(parsed)
    for grade in (10, 11):
        selected_terms = [term for selected_grade, term in ordered if selected_grade == grade]
        if selected_terms and selected_terms != list(range(1, max(selected_terms) + 1)):
            raise DomainError(
                "progression_gap", "Each grade must include earlier terms before later terms.", 422
            )
    current = (int(payload.grade.removeprefix("Grade ")), int(payload.term.removeprefix("Term")))
    if not ordered or ordered[-1] != current:
        raise DomainError(
            "current_progression_mismatch",
            "The current Grade and Term must be the latest progression entry.",
            422,
        )
    return ordered


def _validate_parent(db: Session, parent_id) -> User:
    parent = UserRepository(db).user(parent_id)
    if not parent or parent.role != "parent" or not parent.is_active:
        raise DomainError("invalid_parent", "Choose an active Parent account.", 422)
    return parent


def _validate_subjects(db: Session, subject_ids: set[str]) -> None:
    if not subject_ids or CatalogRepository(db).valid_subject_ids(subject_ids) != subject_ids:
        raise DomainError("invalid_subjects", "Choose valid iGCSE subjects.", 422)


def create_account(db: Session, principal: Principal, payload: CreateAccountRequest) -> AccountResponse:
    progression = parse_progression(payload)
    users = UserRepository(db)
    if users.username_exists(payload.username):
        raise DomainError("username_exists", "That username already exists.", 409)

    parent = None
    subject_ids: set[str] = set()
    if payload.role == "student":
        parent = _validate_parent(db, payload.parentId)
        subject_ids = set(payload.subjects)
        _validate_subjects(db, subject_ids)

    user = User(
        username=payload.username,
        display_name=payload.name,
        role=payload.role,
        password_hash=hash_password(payload.password),
        must_change_password=True,
    )
    db.add(user)
    db.flush()
    if payload.role == "student":
        db.add(StudentProfile(student_id=user.id, parent_id=parent.id))
        StudentRepository(db).replace_enrolment(user.id, progression, subject_ids)
    db.add(AuditEvent(
        actor_id=principal.user.id,
        action="account.created",
        target_type="user",
        target_id=str(user.id),
        event_data={"role": user.role, "username": user.username},
    ))
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DomainError(
            "account_conflict",
            "The account could not be created because its data conflicts with an existing record.",
            409,
        ) from exc
    return AccountResponse(id=str(user.id), username=user.username, name=user.display_name, role=user.role)


def update_student(db: Session, principal: Principal, payload: UpdateStudentRequest) -> dict:
    users = UserRepository(db)
    student = users.user(payload.id)
    profile = users.profile(payload.id)
    if not student or student.role != "student" or not profile:
        raise DomainError("student_not_found", "Student not found.", 404)
    parent = _validate_parent(db, payload.parentId)
    progression = parse_progression(payload)
    subject_ids = set(payload.subjects)
    _validate_subjects(db, subject_ids)

    student.display_name = payload.name
    profile.parent_id = parent.id
    StudentRepository(db).replace_enrolment(student.id, progression, subject_ids)
    db.add(AuditEvent(
        actor_id=principal.user.id,
        action="student.updated",
        target_type="user",
        target_id=str(student.id),
        event_data={
            "parentId": str(parent.id),
            "progression": payload.progression,
            "subjects": sorted(subject_ids),
        },
    ))
    db.commit()
    from app.services.portal import student_rows

    return next(row for row in student_rows(db, principal) if row["id"] == str(student.id))
