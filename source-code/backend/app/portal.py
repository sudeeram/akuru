import re
import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    AuditEvent, Course, StudentProfile, StudentProgression, StudentSubject,
    Subject, User,
)
from app.security import Principal, get_principal, hash_password, require_csrf_roles

router = APIRouter(prefix="/api/v1", tags=["portal"])
GRADES = ("Grade 10", "Grade 11")
TERMS = ("Term1", "Term2", "Term3")
DOCUMENT_KINDS = ("Textbook", "Past paper", "Marking scheme", "Examiner report", "Reference material")
USERNAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{2,39}$")
SUBJECT_PRESENTATION = {
    "english": ("Aa", "#8b5cf6", "Language and literature"),
    "maths": ("∑", "#2563eb", "Number and problem solving"),
    "ict": ("⌘", "#0891b2", "Information and communication technology"),
    "biology": ("🧬", "#16a34a", "Living systems"),
    "chemistry": ("⚗", "#ea580c", "Matter and reactions"),
    "physics": ("⚡", "#7c3aed", "Forces, energy and waves"),
    "french": ("Fr", "#db2777", "French language"),
    "human-biology": ("♡", "#dc2626", "Human systems"),
}


class CreateAccountRequest(BaseModel):
    username: str = Field(min_length=3, max_length=40)
    name: str = Field(min_length=1, max_length=160)
    password: str = Field(min_length=12, max_length=200)
    role: Literal["parent", "student"]
    parentId: uuid.UUID | None = None
    level: Literal["iGCSE"] | None = None
    grade: Literal["Grade 10", "Grade 11"] | None = None
    term: Literal["Term1", "Term2", "Term3"] | None = None
    progression: list[str] = Field(default_factory=list, max_length=6)
    subjects: list[str] = Field(default_factory=list, max_length=8)

    @model_validator(mode="after")
    def validate_student_fields(self):
        self.username = self.username.strip().lower()
        self.name = self.name.strip()
        if not USERNAME_PATTERN.fullmatch(self.username):
            raise ValueError("Username must use 3–40 lowercase letters, numbers, underscores or hyphens.")
        if not self.name:
            raise ValueError("Name is required.")
        if self.role == "student" and not all((self.parentId, self.level, self.grade, self.term, self.progression, self.subjects)):
            raise ValueError("Students require a parent, iGCSE progression, and at least one subject.")
        return self


class UpdateStudentRequest(BaseModel):
    id: uuid.UUID
    name: str = Field(min_length=1, max_length=160)
    parentId: uuid.UUID
    level: Literal["iGCSE"]
    grade: Literal["Grade 10", "Grade 11"]
    term: Literal["Term1", "Term2", "Term3"]
    progression: list[str] = Field(min_length=1, max_length=6)
    subjects: list[str] = Field(min_length=1, max_length=8)

    @model_validator(mode="after")
    def clean_name(self):
        self.name = self.name.strip()
        if not self.name:
            raise ValueError("Name is required.")
        return self


def parse_progression(payload: CreateAccountRequest | UpdateStudentRequest) -> list[tuple[int, int]]:
    if isinstance(payload, CreateAccountRequest) and payload.role != "student":
        return []
    parsed: set[tuple[int, int]] = set()
    for value in payload.progression:
        try:
            grade_name, term_name = value.split("|", 1)
            parsed.add((int(grade_name.removeprefix("Grade ")), int(term_name.removeprefix("Term"))))
        except (ValueError, AttributeError):
            raise HTTPException(status_code=422, detail="Choose valid Grade and Term combinations.")
    if any(grade not in (10, 11) or term not in (1, 2, 3) for grade, term in parsed):
        raise HTTPException(status_code=422, detail="Choose valid Grade and Term combinations.")
    ordered = sorted(parsed)
    for grade in (10, 11):
        selected_terms = [term for selected_grade, term in ordered if selected_grade == grade]
        if selected_terms and selected_terms != list(range(1, max(selected_terms) + 1)):
            raise HTTPException(status_code=422, detail="Each grade must include earlier terms before later terms.")
    current = (int(payload.grade.removeprefix("Grade ")), int(payload.term.removeprefix("Term")))
    if not ordered or ordered[-1] != current:
        raise HTTPException(status_code=422, detail="The current Grade and Term must be the latest progression entry.")
    return ordered


def student_rows(db: Session, principal: Principal) -> list[dict]:
    query = (
        select(User, StudentProfile)
        .join(StudentProfile, StudentProfile.student_id == User.id)
        .order_by(User.display_name)
    )
    if principal.user.role == "parent":
        query = query.where(StudentProfile.parent_id == principal.user.id)
    elif principal.user.role == "student":
        query = query.where(StudentProfile.student_id == principal.user.id)
    rows = db.execute(query).all()
    result = []
    for user, profile in rows:
        progression = db.execute(
            select(StudentProgression)
            .where(StudentProgression.student_id == user.id)
            .order_by(StudentProgression.grade, StudentProgression.term)
        ).scalars().all()
        subject_ids = list(db.execute(
            select(StudentSubject.subject_id)
            .where(StudentSubject.student_id == user.id)
            .order_by(StudentSubject.subject_id)
        ).scalars())
        current = next((row for row in progression if row.is_current), progression[-1] if progression else None)
        result.append({
            "id": str(user.id), "username": user.username, "name": user.display_name,
            "initial": user.display_name[:1].upper(), "parentId": str(profile.parent_id),
            "level": "iGCSE",
            "grade": f"Grade {current.grade}" if current else "",
            "term": f"Term{current.term}" if current else "",
            "progression": [{"grade": f"Grade {row.grade}", "term": f"Term{row.term}"} for row in progression],
            "subjects": subject_ids,
            "courses": {subject_id: {"level": "iGCSE", "syllabus": "Not configured"} for subject_id in subject_ids},
            "needsConfiguration": not bool(current and subject_ids),
        })
    return result


@router.get("/state")
def state(
    principal: Annotated[Principal, Depends(get_principal)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    courses = db.execute(select(Course).order_by(Course.name)).scalars().all()
    subjects = db.execute(select(Subject).order_by(Subject.name)).scalars().all()
    accounts = []
    if principal.user.role == "admin" and not principal.user.must_change_password:
        accounts = [
            {"id": str(user.id), "username": user.username, "name": user.display_name, "role": user.role}
            for user in db.execute(select(User).where(User.role.in_(("parent", "student"))).order_by(User.display_name)).scalars()
        ]
    return {
        "user": {
            "id": str(principal.user.id), "username": principal.user.username,
            "name": principal.user.display_name, "role": principal.user.role,
            "mustChangePassword": principal.user.must_change_password,
        },
        "catalog": {
            "courses": [course.name for course in courses],
            "activeCourses": [course.name for course in courses if course.phase1_active],
            "grades": list(GRADES), "terms": list(TERMS), "kinds": list(DOCUMENT_KINDS),
            "progressionPairs": [{"grade": grade, "term": term} for grade in GRADES for term in TERMS],
        },
        "accounts": accounts,
        "subjects": [
            {"id": subject.id, "name": subject.name, "symbol": SUBJECT_PRESENTATION[subject.id][0],
             "color": SUBJECT_PRESENTATION[subject.id][1], "topic": SUBJECT_PRESENTATION[subject.id][2],
             "topics": [], "course": "iGCSE"}
            for subject in subjects
        ],
        "students": [] if principal.user.must_change_password else student_rows(db, principal),
        "units": [], "coverage": [], "questionBank": [], "drafts": {}, "questions": [],
        "attempts": [], "assignments": [], "documents": [], "exams": [], "reviews": [], "plans": {},
    }


@router.post("/admin/accounts", status_code=status.HTTP_201_CREATED)
def create_account(
    payload: CreateAccountRequest,
    principal: Annotated[Principal, Depends(require_csrf_roles("admin"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    progression = parse_progression(payload)
    if db.execute(select(User.id).where(User.username == payload.username)).scalar_one_or_none():
        raise HTTPException(status_code=409, detail="That username already exists.")

    parent = None
    subject_ids: set[str] = set()
    if payload.role == "student":
        parent = db.get(User, payload.parentId)
        if not parent or parent.role != "parent" or not parent.is_active:
            raise HTTPException(status_code=422, detail="Choose an active Parent account.")
        subject_ids = set(payload.subjects)
        existing_subjects = set(db.execute(select(Subject.id).where(Subject.id.in_(subject_ids))).scalars())
        if not subject_ids or existing_subjects != subject_ids:
            raise HTTPException(status_code=422, detail="Choose valid iGCSE subjects.")

    user = User(
        username=payload.username, display_name=payload.name, role=payload.role,
        password_hash=hash_password(payload.password), must_change_password=True,
    )
    db.add(user)
    db.flush()
    if payload.role == "student":
        db.add(StudentProfile(student_id=user.id, parent_id=parent.id))
        for grade, term in progression:
            db.add(StudentProgression(
                student_id=user.id, course_id="igcse", grade=grade, term=term,
                is_current=(grade, term) == progression[-1],
            ))
        for subject_id in subject_ids:
            db.add(StudentSubject(student_id=user.id, subject_id=subject_id))
    db.add(AuditEvent(
        actor_id=principal.user.id, action="account.created", target_type="user",
        target_id=str(user.id), event_data={"role": user.role, "username": user.username},
    ))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="The account could not be created because its data conflicts with an existing record.")
    return {"id": str(user.id), "username": user.username, "name": user.display_name, "role": user.role}


@router.post("/admin/students")
def update_student(
    payload: UpdateStudentRequest,
    principal: Annotated[Principal, Depends(require_csrf_roles("admin"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    student = db.get(User, payload.id)
    profile = db.get(StudentProfile, payload.id)
    if not student or student.role != "student" or not profile:
        raise HTTPException(status_code=404, detail="Student not found.")
    parent = db.get(User, payload.parentId)
    if not parent or parent.role != "parent" or not parent.is_active:
        raise HTTPException(status_code=422, detail="Choose an active Parent account.")
    progression = parse_progression(payload)
    subject_ids = set(payload.subjects)
    existing_subjects = set(db.execute(select(Subject.id).where(Subject.id.in_(subject_ids))).scalars())
    if existing_subjects != subject_ids:
        raise HTTPException(status_code=422, detail="Choose valid iGCSE subjects.")

    student.display_name = payload.name
    profile.parent_id = parent.id
    for row in db.execute(select(StudentProgression).where(StudentProgression.student_id == student.id)).scalars():
        db.delete(row)
    for row in db.execute(select(StudentSubject).where(StudentSubject.student_id == student.id)).scalars():
        db.delete(row)
    db.flush()
    for grade, term in progression:
        db.add(StudentProgression(
            student_id=student.id, course_id="igcse", grade=grade, term=term,
            is_current=(grade, term) == progression[-1],
        ))
    for subject_id in subject_ids:
        db.add(StudentSubject(student_id=student.id, subject_id=subject_id))
    db.add(AuditEvent(
        actor_id=principal.user.id, action="student.updated", target_type="user",
        target_id=str(student.id),
        event_data={"parentId": str(parent.id), "progression": payload.progression, "subjects": sorted(subject_ids)},
    ))
    db.commit()
    return next(row for row in student_rows(db, principal) if row["id"] == str(student.id))
