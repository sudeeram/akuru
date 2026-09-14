import uuid
from sqlalchemy.orm import Session

from app.repositories.catalog import CatalogRepository
from app.repositories.documents import DocumentRepository
from app.repositories.students import StudentRepository
from app.repositories.users import UserRepository
from app.security import Principal
from app.services import assessments, mastery, study_plans, weaknesses


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
                "edition": document.edition,
            })
    assessment_rows = assessments.list_assessments(db, principal).assessments if principal.user.role == "student" and not principal.user.must_change_password else []
    assessment_questions = []
    assessment_attempts = []
    seen_questions = set()
    exams = []
    for item in assessment_rows:
        ids, answers, files = [], {}, {}
        for question in item.questions:
            qid = str(question.id); ids.append(qid); answers[qid] = question.answer
            if question.fileId: files[qid] = question.fileId
            if qid not in seen_questions:
                seen_questions.add(qid)
                assessment_questions.append({"id": qid, "subject": item.subjectId, "topic": item.title,
                    "title": f"Question {question.number}", "prompt": question.prompt, "marks": question.marks,
                    "type": "written", "diagram": "none", "source": "Frozen approved assessment source",
                    "unitIds": question.unitIds, "rubric": question.rubric, "assetIds": question.assetIds,
                    "assessmentId": str(item.id)})
            if question.result:
                result = question.result
                assessment_attempts.append({"id": str(result.id), "studentId": str(item.studentId),
                    "subject": item.subjectId, "questionId": qid, "title": f"Question {question.number}",
                    "answer": question.answer, "fileId": str(question.fileId or ""), "hints": 0,
                    "mark": None if result.status == "needs_review" else result.awardedMarks, "maxMarks": result.maxMarks,
                    "status": "needs-review" if result.status == "needs_review" else "assessed",
                    "feedback": " ".join(result.strengths + result.smallMistakes + result.conceptualMistakes),
                    "explanation": result.teachingExplanation,
                    "points": [decision.rationale for decision in result.markingDecisions],
                    "createdAt": result.createdAt.isoformat(), "examId": str(item.id) if item.mode != "practice" else None,
                    "improvedAnswer": result.improvedAnswer, "recommendations": result.recommendations,
                    "assessmentId": str(item.id),
                    "workingUrl": f"/api/v1/assessments/{item.id}/working/{question.fileId}" if question.fileId else None})
        exams.append({"id": str(item.id), "studentId": str(item.studentId), "subject": item.subjectId,
            "mode": item.mode, "status": item.status, "startedAt": item.startedAt.isoformat(),
            "endsAt": item.endsAt.isoformat(), "questionIds": ids, "answers": answers, "files": files,
            "feedbackVisible": item.feedbackVisible})
    visible_students = student_rows(db, principal) if not principal.user.must_change_password else []
    mastery_rows = ({row["id"]: [unit.model_dump(mode="json") for unit in mastery.list_mastery(
        db, principal, uuid.UUID(row["id"])).units] for row in visible_students}
        if principal.user.role in {"student", "parent"} else {})
    recommendation_rows = ({row["id"]: [item.model_dump(mode="json") for item in weaknesses.list_recommendations(
        db, principal, uuid.UUID(row["id"])).recommendations] for row in visible_students}
        if principal.user.role in {"student", "parent"} else {})
    plan_rows = ({row["id"]: study_plans.current(db, principal, uuid.UUID(row["id"])).model_dump(mode="json")
        for row in visible_students} if principal.user.role in {"student", "parent"} else {})
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
        "students": visible_students,
        "units": [],
        "coverage": [],
        "questionBank": [],
        "drafts": {},
        "questions": assessment_questions,
        "attempts": assessment_attempts,
        "assignments": [],
        "documents": portal_documents,
        "exams": exams,
        "assessmentBlueprints": [row.model_dump(mode="json") for row in assessments.list_blueprints(db, principal)] if principal.user.role in {"admin", "student"} and not principal.user.must_change_password else [],
        "officialPapers": assessments.official_papers(db, principal.user.id) if principal.user.role == "student" and not principal.user.must_change_password else [],
        "reviews": [],
        "plans": plan_rows,
        "mastery": mastery_rows,
        "recommendations": recommendation_rows,
    }
