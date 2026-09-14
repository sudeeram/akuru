import hashlib
import uuid
from pathlib import PurePath

from sqlalchemy.orm import Session

from app.config import Settings
from app.errors import DomainError
from app.models import Assessment, AssessmentQuestion, AssessmentWorkingFile, StudentProfile
from app.schemas.assessments import WorkingFileResponse
from app.security import Principal
from app.services.assessments import _owned
from app.services.document_extraction import extract_document
from app.services.document_processing_types import ProcessingFailure
from app.services.documents import validate_file
from app.storage import ObjectStorage


def response(row: AssessmentWorkingFile, settings: Settings) -> WorkingFileResponse:
    return WorkingFileResponse(id=row.id, name=row.original_filename, contentType=row.content_type,
        ocrText=row.ocr_text, ocrConfidence=row.ocr_confidence,
        needsReview=row.ocr_confidence < settings.assessment_ocr_review_threshold)


def upload(db: Session, storage: ObjectStorage, settings: Settings, principal: Principal,
           assessment_id: uuid.UUID, question_id: uuid.UUID, content: bytes,
           filename: str, content_type: str) -> WorkingFileResponse:
    assessment = _owned(db, principal, assessment_id, True)
    if assessment.status != "active":
        raise DomainError("assessment_not_active", "Working can only be uploaded while the assessment is active.", 409)
    question = db.get(AssessmentQuestion, question_id)
    if not question or question.assessment_id != assessment.id:
        raise DomainError("assessment_question_not_found", "Question not found in this assessment.", 404)
    if len(content) > settings.assessment_working_max_bytes:
        raise DomainError("working_too_large", f"Working must be {settings.assessment_working_max_bytes // (1024 * 1024)} MB or smaller.", 413)
    normalized = validate_file(filename, content_type, content)
    file_id = uuid.uuid4(); extension = PurePath(filename).suffix.lower()
    object_key = f"student-working/{principal.user.id}/{assessment.id}/{question.id}/{file_id}{extension}"
    try:
        extracted = extract_document(content, normalized, assessment.subject_id, 10,
            settings.document_render_dpi, 1, settings.tesseract_command)
        blocks = [block for page in extracted["pages"] for block in page["blocks"] if block.get("text")]
        ocr_text = "\n".join(block["text"] for block in blocks)
        confidence = min((float(block.get("confidence", 0)) for block in blocks), default=0)
        metadata = {"method": "document_extraction", "pageCount": extracted["pageCount"],
            "blockCount": len(blocks), "needsReview": confidence < settings.assessment_ocr_review_threshold}
    except ProcessingFailure as exc:
        ocr_text, confidence = "", 0
        metadata = {"method": "failed", "errorCode": exc.code, "needsReview": True}
    storage.put(object_key, content, normalized)
    row = AssessmentWorkingFile(id=file_id, assessment_id=assessment.id, question_id=question.id,
        student_id=principal.user.id, original_filename=filename, content_type=normalized,
        byte_size=len(content), checksum=hashlib.sha256(content).hexdigest(), object_key=object_key,
        ocr_text=ocr_text, ocr_confidence=confidence, ocr_metadata=metadata)
    db.add(row); db.commit(); db.refresh(row)
    return response(row, settings)


def owned(db: Session, principal: Principal, assessment_id: uuid.UUID, file_id: uuid.UUID) -> AssessmentWorkingFile:
    assessment = db.get(Assessment, assessment_id)
    profile = db.get(StudentProfile, assessment.student_id) if assessment else None
    allowed = bool(assessment and (principal.user.role == "admin" or principal.user.id == assessment.student_id or
        (principal.user.role == "parent" and profile and profile.parent_id == principal.user.id)))
    if not allowed:
        raise DomainError("working_not_found", "Submitted working not found.", 404)
    row = db.get(AssessmentWorkingFile, file_id)
    if not row or row.assessment_id != assessment_id or row.student_id != assessment.student_id:
        raise DomainError("working_not_found", "Submitted working not found.", 404)
    return row
