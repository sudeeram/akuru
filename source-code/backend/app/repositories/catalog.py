from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Course, Subject


class CatalogRepository:
    def __init__(self, db: Session):
        self.db = db

    def courses(self) -> list[Course]:
        return list(self.db.execute(select(Course).order_by(Course.name)).scalars())

    def subjects(self) -> list[Subject]:
        return list(self.db.execute(select(Subject).order_by(Subject.name)).scalars())

    def valid_subject_ids(self, subject_ids: set[str]) -> set[str]:
        if not subject_ids:
            return set()
        return set(self.db.execute(select(Subject.id).where(Subject.id.in_(subject_ids))).scalars())
