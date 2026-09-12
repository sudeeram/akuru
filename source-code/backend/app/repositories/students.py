import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import StudentProfile, StudentProgression, StudentSubject, User


class StudentRepository:
    def __init__(self, db: Session):
        self.db = db

    def visible_students(self, role: str, user_id: uuid.UUID) -> list[tuple[User, StudentProfile]]:
        query = select(User, StudentProfile).join(
            StudentProfile, StudentProfile.student_id == User.id
        ).order_by(User.display_name)
        if role == "parent":
            query = query.where(StudentProfile.parent_id == user_id)
        elif role == "student":
            query = query.where(StudentProfile.student_id == user_id)
        return list(self.db.execute(query).all())

    def progression(self, student_id: uuid.UUID) -> list[StudentProgression]:
        return list(self.db.execute(select(StudentProgression).where(
            StudentProgression.student_id == student_id
        ).order_by(StudentProgression.grade, StudentProgression.term)).scalars())

    def subject_ids(self, student_id: uuid.UUID) -> list[str]:
        return list(self.db.execute(select(StudentSubject.subject_id).where(
            StudentSubject.student_id == student_id
        ).order_by(StudentSubject.subject_id)).scalars())

    def replace_enrolment(
        self,
        student_id: uuid.UUID,
        progression: list[tuple[int, int]],
        subject_ids: set[str],
    ) -> None:
        for row in self.db.execute(select(StudentProgression).where(
            StudentProgression.student_id == student_id
        )).scalars():
            self.db.delete(row)
        for row in self.db.execute(select(StudentSubject).where(
            StudentSubject.student_id == student_id
        )).scalars():
            self.db.delete(row)
        self.db.flush()
        for grade, term in progression:
            self.db.add(StudentProgression(
                student_id=student_id,
                course_id="igcse",
                grade=grade,
                term=term,
                is_current=(grade, term) == progression[-1],
            ))
        for subject_id in subject_ids:
            self.db.add(StudentSubject(student_id=student_id, subject_id=subject_id))
