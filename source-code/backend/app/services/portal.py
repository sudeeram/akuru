from sqlalchemy.orm import Session

from app.repositories.catalog import CatalogRepository
from app.repositories.documents import DocumentRepository
from app.repositories.students import StudentRepository
from app.repositories.users import UserRepository
from app.security import Principal


GRADES = ("Grade 10", "Grade 11")
TERMS = ("Term1", "Term2", "Term3")
DOCUMENT_KINDS = ("Textbook", "Past paper", "Marking scheme", "Examiner report", "Reference material")
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


def student_rows(db: Session, principal: Principal) -> list[dict]:
    repository = StudentRepository(db)
    result = []
    for user, profile in repository.visible_students(principal.user.role, principal.user.id):
        progression = repository.progression(user.id)
        subject_ids = repository.subject_ids(user.id)
        current = next((row for row in progression if row.is_current), progression[-1] if progression else None)
        result.append({
            "id": str(user.id),
            "username": user.username,
            "name": user.display_name,
            "initial": user.display_name[:1].upper(),
            "parentId": str(profile.parent_id),
            "level": "iGCSE",
            "grade": f"Grade {current.grade}" if current else "",
            "term": f"Term{current.term}" if current else "",
            "progression": [
                {"grade": f"Grade {row.grade}", "term": f"Term{row.term}"} for row in progression
            ],
            "subjects": subject_ids,
            "courses": {
                subject_id: {"level": "iGCSE", "syllabus": "Not configured"}
                for subject_id in subject_ids
            },
            "needsConfiguration": not bool(current and subject_ids),
        })
    return result


def get_portal_state(db: Session, principal: Principal) -> dict:
    catalog = CatalogRepository(db)
    courses = catalog.courses()
    subjects = catalog.subjects()
    accounts = []
    if principal.user.role == "admin" and not principal.user.must_change_password:
        accounts = [
            {"id": str(user.id), "username": user.username, "name": user.display_name, "role": user.role}
            for user in UserRepository(db).portal_accounts()
        ]
    document_kind_labels = {
        "textbook": "Textbook",
        "reference": "Reference material",
        "past_paper": "Past paper",
        "mark_scheme": "Marking scheme",
        "examiner_report": "Examiner report",
    }
    portal_documents = []
    if principal.user.role == "admin" and not principal.user.must_change_password:
        portal_documents = []
        document_repository = DocumentRepository(db)
        for document, _version in document_repository.active_documents():
            job = document_repository.latest_job(document.id)
            portal_documents.append({
                "id": str(document.id),
                "name": document.title,
                "subject": document.subject_id,
                "course": "iGCSE",
                "kind": document_kind_labels[document.kind],
                "status": job.status if job else document.review_state,
                "notes": "",
                "paperId": str(document.source_document_id) if document.source_document_id else None,
                "processingProgress": job.progress if job else 0,
                "processingError": job.error_message if job else None,
            })
    return {
        "user": {
            "id": str(principal.user.id),
            "username": principal.user.username,
            "name": principal.user.display_name,
            "role": principal.user.role,
            "mustChangePassword": principal.user.must_change_password,
        },
        "catalog": {
            "courses": [course.name for course in courses],
            "activeCourses": [course.name for course in courses if course.phase1_active],
            "grades": list(GRADES),
            "terms": list(TERMS),
            "kinds": list(DOCUMENT_KINDS),
            "progressionPairs": [{"grade": grade, "term": term} for grade in GRADES for term in TERMS],
        },
        "accounts": accounts,
        "subjects": [
            {
                "id": subject.id,
                "name": subject.name,
                "symbol": SUBJECT_PRESENTATION[subject.id][0],
                "color": SUBJECT_PRESENTATION[subject.id][1],
                "topic": SUBJECT_PRESENTATION[subject.id][2],
                "topics": [],
                "course": "iGCSE",
            }
            for subject in subjects
        ],
        "students": [] if principal.user.must_change_password else student_rows(db, principal),
        "units": [],
        "coverage": [],
        "questionBank": [],
        "drafts": {},
        "questions": [],
        "attempts": [],
        "assignments": [],
        "documents": portal_documents,
        "exams": [],
        "reviews": [],
        "plans": {},
    }
