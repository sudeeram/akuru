from sqlalchemy.orm import Session

from app.repositories.catalog import CatalogRepository
from app.schemas.curriculum import CatalogResponse, CourseResponse, SubjectResponse


def get_catalog(db: Session) -> CatalogResponse:
    repository = CatalogRepository(db)
    return CatalogResponse(
        courses=[CourseResponse(id=row.id, name=row.name, phase1Active=row.phase1_active) for row in repository.courses()],
        subjects=[SubjectResponse(id=row.id, name=row.name) for row in repository.subjects()],
    )
