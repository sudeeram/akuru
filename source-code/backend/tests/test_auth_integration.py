import base64
import json
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pymupdf as fitz
import pytest
from pydantic import SecretStr
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import engine, get_db
from app.main import app
from app.models import (
    AIInvocation, AIProviderAccount, Assessment, AssessmentAnswer, AssessmentBlueprint, AssessmentCurriculumSnapshot, AssessmentQuestion, AssessmentResult, AuditEvent, CurriculumPlan, Document, DocumentAsset, DocumentBlock, DocumentEvent, DocumentJob,
    DocumentPage, DocumentVersion, StudentAIQuota, StudentAIUsage, StudentProfile,
    ExaminerCommentVersion, MarkSchemeEntryVersion, OfficialMaterialVersion, OfficialQuestionTopicMapping, OfficialQuestionVersion,
    RetrievalChunk, CurriculumPlanTopic, StudentProgression, StudentSubject,
    AuthSession, EducationalMedia, EvaluationCorpus, EvaluationRelease, EvaluationRun, FamilyUsageEvent, ImprovementRecommendation, PasswordResetReceipt, StudyPlan, StudyPlanItem, Textbook, TextbookGroup, TextbookStructureVersion, TextbookTopic, TextbookTopicContentVersion, TextbookTopicDocument, TutorLearnerContextLog, TutorProfile, TutorProfileVersion, TutorRealtimeConnection, TutorSafetyEvent, TutorSession, TutorSessionProfileEvent, TutorSessionSummary, TutorTurn, User, WeaknessDiagnosis,
)
from app.security import hash_password
from app.services.curriculum_plans import snapshot
from app.queue.factory import get_document_queue
from app.services import document_processing
from app.services import assessment_marking
from app.services import assessment_working
from app.services import weaknesses
from app.services import assessments
from app.services import documents as document_service
from app.services import tutor_agent
from app.services import tutor_realtime
from app.config import Settings, get_settings
from app.ai.base import AIResult, AIUsage
from app.storage.factory import get_storage
from app.storage.local import LocalObjectStorage
from app.services.embeddings import embed_texts


class FakeDocumentQueue:
    def __init__(self):
        self.job_ids: list[uuid.UUID] = []

    def enqueue(self, job_id: uuid.UUID) -> None:
        self.job_ids.append(job_id)

    def dequeue(self, timeout_seconds: int = 5) -> uuid.UUID | None:
        return self.job_ids.pop(0) if self.job_ids else None


def _create_quota_test_student(client, headers, parent_id: str, suffix: str) -> tuple[dict, str]:
    password = f"temporary student password {suffix}"
    response = client.post("/api/v1/admin/accounts", headers=headers, json={
        "username": f"quota-{suffix}", "name": f"Quota Student {suffix}", "password": password,
        "role": "student", "parentId": parent_id, "level": "iGCSE", "grade": "Grade 10",
        "term": "Term1", "progression": ["Grade 10|Term1"], "subjects": ["maths"],
    })
    assert response.status_code == 201
    return response.json(), password


@pytest.fixture
def auth_client(tmp_path):
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    username = f"test-admin-{uuid.uuid4().hex}"
    password = "correct horse battery staple"
    session.add(User(
        username=username,
        display_name="Security Test Admin",
        role="admin",
        password_hash=hash_password(password),
        must_change_password=False,
    ))
    session.commit()

    def override_db():
        yield session

    storage = LocalObjectStorage(tmp_path / "private-documents")
    queue = FakeDocumentQueue()

    def override_storage():
        return storage

    def override_queue():
        return queue

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_storage] = override_storage
    app.dependency_overrides[get_document_queue] = override_queue
    client = TestClient(app, base_url="http://localhost")
    try:
        yield client, username, password
    finally:
        app.dependency_overrides.clear()
        session.close()
        transaction.rollback()
        connection.close()


@pytest.mark.integration
def test_login_protected_routes_and_logout(auth_client) -> None:
    client, username, password = auth_client
    assert client.get("/api/v1/catalog").status_code == 401
    assert client.get("/api/v1/assessments/admin/audit").status_code == 401
    assert client.get("/api/v1/operations/admin/status").status_code == 401
    assert client.post("/api/v1/auth/login", json={"username": username, "password": "wrong-password"}).status_code == 401

    login = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert login.status_code == 200
    payload = login.json()
    assert client.get("/api/v1/operations/admin/status").status_code == 200
    assert client.get("/api/v1/assessments/admin/audit").status_code == 200
    assert payload["user"] == {
        "id": payload["user"]["id"], "username": username,
        "name": "Security Test Admin", "role": "admin",
        "mustChangePassword": False,
    }
    assert "password_hash" not in payload["user"]
    assert "password" not in payload["user"]
    assert "HttpOnly" in login.headers["set-cookie"]
    assert "SameSite=strict" in login.headers["set-cookie"]

    assert client.get("/api/v1/auth/me").status_code == 200
    ui_features = client.get("/api/v1/admin/ui-features")
    assert ui_features.status_code == 200
    assert ui_features.json()["allowed"] is True
    assert ui_features.json()["user"]["role"] == "admin"
    assert client.get("/ready").json() == {"status": "ready", "database": "connected"}
    catalog = client.get("/api/v1/catalog")
    assert catalog.status_code == 200
    assert [course["id"] for course in catalog.json()["courses"] if course["phase1Active"]] == ["igcse"]

    assert client.post("/api/v1/auth/logout").status_code == 403
    logout = client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": payload["csrfToken"]})
    assert logout.status_code == 204
    assert client.get("/api/v1/auth/me").status_code == 401


@pytest.mark.integration
def test_rejects_untrusted_origins(auth_client) -> None:
    client, username, password = auth_client
    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
        headers={"Origin": "https://attacker.example"},
    )
    assert response.status_code == 403
    assert response.json() == {
        "error": {"code": "origin_not_allowed", "message": "Origin not allowed.", "details": []}
    }

    known = client.post("/api/v1/auth/login", json={
        "username": username, "password": "wrong-password"})
    unknown = client.post("/api/v1/auth/login", json={
        "username": f"unknown-{uuid.uuid4().hex}", "password": "wrong-password"})
    assert known.status_code == unknown.status_code == 401
    assert known.json() == unknown.json() == {
        "error": {"code": "invalid_credentials",
                  "message": "The username or password is incorrect.", "details": []}}


@pytest.mark.integration
def test_review_completion_handles_page_only_unattached_and_terminal_documents(auth_client) -> None:
    client, username, password = auth_client
    login = client.post("/api/v1/auth/login", json={"username": username, "password": password}).json()
    headers = {"X-CSRF-Token": login["csrfToken"]}
    session = next(app.dependency_overrides[get_db]())
    admin = session.scalar(select(User).where(User.username == username))

    def document_version(label: str, review_state: str = "pending", status: str = "needs_review"):
        token = uuid.uuid4().hex
        document = Document(kind="textbook", course_id="igcse", subject_id="chemistry",
            title=label, original_filename=f"{label}.pdf", object_key=f"tests/{token}.pdf",
            mime_type="application/pdf", sha256=(token * 2)[:64], review_state=review_state,
            uploaded_by=admin.id, size_bytes=10)
        session.add(document); session.flush()
        version = DocumentVersion(document_id=document.id, version_number=1,
            original_filename=f"{label}.pdf", object_key=f"tests/{token}-v1.pdf",
            mime_type="application/pdf", sha256=((token[::-1]) * 2)[:64],
            size_bytes=10, status=status, uploaded_by=admin.id)
        session.add(version); session.flush()
        asset = DocumentAsset(document_version_id=version.id, asset_kind="page_render",
            object_key=f"tests/{token}.png", mime_type="image/png", sha256=(token * 2)[:64],
            size_bytes=10, page_number=1, bounding_box={})
        session.add(asset); session.flush()
        page = DocumentPage(document_version_id=version.id, page_number=1,
            width_points=100, height_points=100, render_asset_id=asset.id,
            native_text="", extraction_method="native", confidence=1.0, needs_review=True,
            page_metadata={})
        session.add(page); session.commit()
        return document, version, page

    document, version, page = document_version("page-only")
    response = client.post(f"/api/v1/documents/{document.id}/extraction/pages/{page.id}",
                           headers=headers, json={"printedPageLabel": "1"})
    assert response.status_code == 200
    session.refresh(document); session.refresh(version)
    assert document.review_state == "reviewed" and version.status == "completed"
    assert session.scalar(select(DocumentEvent).where(
        DocumentEvent.document_version_id == version.id,
        DocumentEvent.event_type == "extraction_review_completed"))

    for label, review_state, status in (
        ("published-terminal", "published", "completed"),
        ("rejected-terminal", "rejected", "completed"),
        ("failed-terminal", "pending", "failed"),
        ("removed-terminal", "pending", "removed"),
    ):
        terminal_document, terminal_version, terminal_page = document_version(
            label, review_state, status)
        terminal_page.needs_review = False; session.commit()
        document_service._refresh_topic_document_readiness(session, terminal_version.id, admin.id)
        session.commit(); session.refresh(terminal_document); session.refresh(terminal_version)
        assert terminal_document.review_state == review_state
        assert terminal_version.status == status


@pytest.mark.integration
def test_admin_configures_canonical_source_and_reviews_visual_assets(auth_client) -> None:
    client, username, password = auth_client
    login = client.post("/api/v1/auth/login", json={"username": username, "password": password}).json()
    headers = {"X-CSRF-Token": login["csrfToken"]}
    session = next(app.dependency_overrides[get_db]())
    admin = session.scalar(select(User).where(User.username == username))
    token = uuid.uuid4().hex
    book = Textbook(course_id="igcse", subject_id="chemistry", title=f"Visual test {token}",
        edition="2026", publisher="AKURU", group_label="unit", status="published",
        created_by=admin.id, published_by=admin.id, published_at=datetime.now(timezone.utc))
    session.add(book); session.flush()
    group = TextbookGroup(textbook_id=book.id, code="U1", title="Unit 1", summary="",
        sequence=1, status="published")
    session.add(group); session.flush()
    topic = TextbookTopic(textbook_id=book.id, group_id=group.id, course_id="igcse",
        subject_id="chemistry", code="1", title="States of Matter", sequence=1,
        status="published", published_at=datetime.now(timezone.utc))
    session.add(topic); session.flush()

    def source(filename: str, sequence: int):
        local = uuid.uuid4().hex
        document = Document(kind="textbook", course_id="igcse", subject_id="chemistry",
            title=filename, original_filename=filename, object_key=f"tests/{local}.pdf",
            mime_type="application/pdf", sha256=(local * 2)[:64], review_state="reviewed",
            uploaded_by=admin.id, size_bytes=10)
        session.add(document); session.flush()
        version = DocumentVersion(document_id=document.id, version_number=1,
            original_filename=filename, object_key=f"tests/{local}-v1.pdf",
            mime_type="application/pdf", sha256=(local[::-1] * 2)[:64],
            size_bytes=10, status="completed", uploaded_by=admin.id)
        session.add(version); session.flush()
        session.add(DocumentJob(document_id=document.id, document_version_id=version.id,
            stage="complete", status="completed", progress=100, attempt_count=1,
            extraction_version="test-v1", result_data={}, max_seconds=30, max_memory_mb=128,
            max_pages=10, completed_at=datetime.now(timezone.utc)))
        session.add(TextbookTopicDocument(topic_id=topic.id, document_version_id=version.id,
            document_id=document.id, role="primary", sequence=sequence, review_status="ready",
            created_by=admin.id))
        session.flush()
        return document, version

    clean_document, clean_version = source(
        "Edexcel-iGCSE-Chemistry-Unit-1-Topic-1-States-of-Matter-v2.1.pdf", 1)
    scan_document, scan_version = source(
        "Edexcel-iGCSE-Chemistry-Unit-1-Topic-1-States-of-Matter.pdf", 2)
    clean_render = DocumentAsset(document_version_id=clean_version.id, asset_kind="page_render",
        object_key=f"tests/{token}-clean.png", mime_type="image/png", sha256=("c" * 64),
        size_bytes=10, page_number=1, bounding_box={})
    session.add(clean_render); session.flush()
    clean_page = DocumentPage(document_version_id=clean_version.id, page_number=1,
        printed_page_label="1", width_points=100, height_points=100,
        render_asset_id=clean_render.id, native_text="Matter exists as solid, liquid and gas.",
        extraction_method="native", confidence=1.0, needs_review=False, page_metadata={})
    session.add(clean_page); session.flush()
    session.add(DocumentBlock(document_version_id=clean_version.id, page_id=clean_page.id,
        sequence_number=1, block_kind="paragraph",
        text="Matter exists as solid, liquid and gas.", bounding_box={"x": 1},
        extraction_method="native", confidence=1.0, needs_review=False, block_metadata={}))
    render = DocumentAsset(document_version_id=scan_version.id, asset_kind="page_render",
        object_key=f"tests/{token}-render.png", mime_type="image/png", sha256=("a" * 64),
        size_bytes=10, page_number=1, bounding_box={})
    crop = DocumentAsset(document_version_id=scan_version.id, asset_kind="diagram",
        object_key=f"tests/{token}-diagram.png", mime_type="image/png", sha256=("b" * 64),
        size_bytes=10, page_number=1, bounding_box={"x": 1})
    session.add_all([render, crop]); session.flush()
    page = DocumentPage(document_version_id=scan_version.id, page_number=1,
        width_points=100, height_points=100, render_asset_id=render.id, native_text="",
        extraction_method="ocr", confidence=.9, needs_review=True, page_metadata={})
    session.add(page); session.flush()
    block = DocumentBlock(document_version_id=scan_version.id, page_id=page.id,
        sequence_number=1, block_kind="diagram", text="Particle arrangement",
        bounding_box={"x": 1}, extraction_method="ocr", confidence=.9,
        needs_review=False, source_asset_id=crop.id, block_metadata={})
    session.add(block); session.commit()

    saved_caption = client.post(f"/api/v1/documents/{scan_document.id}/extraction/blocks/{block.id}",
        headers=headers, json={"kind": "diagram", "text": "", "latex": None,
            "caption": "Figure 1.4 The arrangement of particles in different states of matter",
            "sequenceNumber": 1})
    assert saved_caption.status_code == 200, saved_caption.text
    saved_block = saved_caption.json()["pages"][0]["blocks"][0]
    assert saved_block["metadata"]["reviewedCaption"].startswith("Figure 1.4")

    roles = client.post(
        f"/api/v1/admin/textbooks/{book.public_ref}/topics/{topic.public_ref}/sources/apply-recommended-roles",
        headers=headers)
    assert roles.status_code == 200, roles.text
    by_name = {row["filename"]: row for row in roles.json()}
    assert by_name[clean_document.original_filename]["role"] == "primary"
    assert by_name[scan_document.original_filename]["role"] == "visual_reference"
    assert by_name[scan_document.original_filename]["includedInRetrieval"] is False

    url = (f"/api/v1/admin/textbooks/{book.public_ref}/topics/{topic.public_ref}"
           f"/sources/{scan_document.id}/visual-assets")
    candidates = client.get(url)
    assert candidates.status_code == 200 and len(candidates.json()) == 1
    candidate = candidates.json()[0]
    assert candidate["status"] == "unselected" and candidate["page"] == 1
    assert candidate["extractedCaption"].startswith("Figure 1.4")
    missing_alt = client.patch(f"{url}/{candidate['assetRef']}", headers=headers,
        json={"status": "approved", "caption": "Particles", "altText": ""})
    assert missing_alt.status_code == 422
    selected = client.patch(f"{url}/{candidate['assetRef']}", headers=headers,
        json={"status": "selected", "caption": "Particles", "altText": ""})
    assert selected.status_code == 200 and selected.json()[0]["status"] == "selected"
    checklist = client.get(
        f"/api/v1/admin/textbooks/{book.public_ref}/topics/{topic.public_ref}/review-checklist")
    assert checklist.status_code == 200 and checklist.json()["pendingVisualAssets"] == 1
    blocked = client.post(
        f"/api/v1/admin/textbooks/{book.public_ref}/topics/{topic.public_ref}/publish",
        headers=headers, json={"confirmSources": True, "confirmExtraction": True, "confirmTopic": True})
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "topic_content_not_ready"
    approved = client.patch(f"{url}/{selected.json()[0]['assetRef']}", headers=headers,
        json={"status": "approved", "caption": "Particle arrangement",
              "altText": "A labelled diagram comparing particle spacing in solids, liquids and gases."})
    assert approved.status_code == 200 and approved.json()[0]["status"] == "approved"
    checklist = client.get(
        f"/api/v1/admin/textbooks/{book.public_ref}/topics/{topic.public_ref}/review-checklist")
    assert checklist.json()["pendingVisualAssets"] == 0
    refreshed_sources = client.get(
        f"/api/v1/admin/textbooks/{book.public_ref}/topics/{topic.public_ref}/sources").json()
    scan = next(row for row in refreshed_sources if row["documentId"] == str(scan_document.id))
    assert scan["approvedVisualCount"] == 1 and scan["pendingVisualCount"] == 0
    published = client.post(
        f"/api/v1/admin/textbooks/{book.public_ref}/topics/{topic.public_ref}/publish",
        headers=headers, json={"confirmSources": True, "confirmExtraction": True, "confirmTopic": True})
    assert published.status_code == 200, published.text
    content = session.scalar(select(TextbookTopicContentVersion).where(
        TextbookTopicContentVersion.topic_id == topic.id,
        TextbookTopicContentVersion.status == "published"))
    assert content.extraction_manifest["visualAssets"][0]["documentVersionId"] == str(scan_version.id)
    assert content.extraction_manifest["visualAssets"][0]["altText"].startswith("A labelled diagram")
    assert any(row["role"] == "visual_reference" for row in content.source_manifest)
    active_chunks = session.scalars(select(RetrievalChunk).where(
        RetrievalChunk.topic_content_version_id == content.id,
        RetrievalChunk.status == "active")).all()
    assert active_chunks and {row.document_id for row in active_chunks} == {clean_document.id}


@pytest.mark.integration
def test_admin_builds_reorders_versions_and_attaches_scanned_topic_parts(auth_client, monkeypatch) -> None:
    client, username, password = auth_client
    assert client.get("/api/v1/admin/textbooks").status_code == 401
    login = client.post("/api/v1/auth/login", json={"username": username, "password": password}).json()
    headers = {"X-CSRF-Token": login["csrfToken"]}

    created = client.post("/api/v1/admin/textbooks", headers=headers, json={
        "courseId": "igcse", "subjectId": "chemistry", "title": "Chemistry Student Book",
        "edition": "2026", "publisher": "AKURU test", "groupLabel": "unit",
    })
    assert created.status_code == 201, created.text
    book = created.json(); book_ref = book["textbookRef"]
    assert book_ref.startswith("book_") and "id" not in book
    assert book["groupDisplayLabel"] == "Unit"
    duplicate = client.post("/api/v1/admin/textbooks", headers=headers, json={
        "courseId": "igcse", "subjectId": "chemistry", "title": "Chemistry Student Book",
        "edition": "2026", "publisher": "Other", "groupLabel": "unit",
    })
    assert duplicate.status_code == 409

    for sequence, code in enumerate(("U1", "U2"), 1):
        response = client.post(f"/api/v1/admin/textbooks/{book_ref}/groups", headers=headers, json={
            "code": code, "title": f"Unit {sequence}", "summary": "", "sequence": sequence,
        })
        assert response.status_code == 200, response.text
        book = response.json()
    first_group, second_group = book["groups"]
    assert "id" not in first_group

    for group, code in ((first_group, "1"), (second_group, "11")):
        response = client.post(
            f"/api/v1/admin/textbooks/{book_ref}/groups/{group['groupRef']}/topics",
            headers=headers, json={"code": code, "title": f"Topic {code}", "sequence": 1,
                                   "syllabusRef": "", "description": ""},
        )
        assert response.status_code == 200, response.text
        book = response.json()
    refs = [group["groupRef"] for group in reversed(book["groups"])]
    reordered = client.post(f"/api/v1/admin/textbooks/{book_ref}/groups/reorder", headers=headers,
                            json={"refs": refs})
    assert reordered.status_code == 200, reordered.text
    assert [group["groupRef"] for group in reordered.json()["groups"]] == refs

    invalid = client.post(f"/api/v1/admin/textbooks/{book_ref}/publish", headers=headers, json={
        "confirmCourse": True, "confirmSubject": True, "confirmEdition": True, "confirmStructure": False,
    })
    assert invalid.status_code == 422
    confirmation = {"confirmCourse": True, "confirmSubject": True,
                    "confirmEdition": True, "confirmStructure": True}
    published = client.post(f"/api/v1/admin/textbooks/{book_ref}/publish", headers=headers, json=confirmation)
    assert published.status_code == 200, published.text
    assert published.json()["status"] == "published" and published.json()["structureVersion"] == 1

    group = published.json()["groups"][0]
    changed = client.post(f"/api/v1/admin/textbooks/{book_ref}/groups/{group['groupRef']}", headers=headers,
                          json={"code": group["code"], "title": group["title"] + " revised",
                                "summary": "", "sequence": group["sequence"]})
    assert changed.status_code == 200 and changed.json()["status"] == "draft"
    republished = client.post(f"/api/v1/admin/textbooks/{book_ref}/publish", headers=headers, json=confirmation)
    assert republished.status_code == 200 and republished.json()["structureVersion"] == 2

    session = next(app.dependency_overrides[get_db]())
    textbook = session.scalar(select(Textbook).where(Textbook.public_ref == book_ref))
    versions = session.scalars(select(TextbookStructureVersion).where(
        TextbookStructureVersion.textbook_id == textbook.id,
    ).order_by(TextbookStructureVersion.version_number)).all()
    assert len(versions) == 2
    assert versions[0].snapshot["groups"][1]["title"] == "Unit 1"
    assert versions[1].snapshot["groups"][0]["title"].endswith("revised")
    actions = set(session.scalars(select(AuditEvent.action).where(
        AuditEvent.target_id.in_([book_ref, group["groupRef"]]),
    )).all())
    assert "textbook.created" in actions and "textbook_structure.published" in actions

    topic_ref = republished.json()["groups"][0]["topics"][0]["topicRef"]
    scan_pdf = fitz.open(); scan_page = scan_pdf.new_page(); scan_page.insert_text((72, 72), "H2SO4 + NaOH → salt", fontsize=16)
    scan_bytes = scan_pdf.tobytes(); scan_pdf.close()
    upload_headers = {**headers, "X-Filename": "topic-11-acids.pdf", "Content-Type": "application/pdf",
                      "Idempotency-Key": "topic-11-first-part"}
    upload = client.post(f"/api/v1/admin/textbooks/{book_ref}/topics/{topic_ref}/documents",
                         params={"role": "primary", "printedStartPage": "101", "printedEndPage": "104"},
                         headers=upload_headers, content=scan_bytes)
    assert upload.status_code == 201, upload.text
    repeated = client.post(f"/api/v1/admin/textbooks/{book_ref}/topics/{topic_ref}/documents",
                           params={"role": "primary"}, headers=upload_headers, content=scan_bytes)
    assert repeated.status_code == 201 and repeated.json()["document"]["id"] == upload.json()["document"]["id"]
    suggestions = client.post(f"/api/v1/admin/textbooks/{book_ref}/topics/suggest", headers=headers,
                              json={"filenames": ["topic-11-neutralisation.pdf"]})
    assert suggestions.status_code == 200 and suggestions.json()[0]["suggestedTopicRef"] == topic_ref
    version_id = uuid.UUID(upload.json()["document"]["versionId"])
    link = session.scalar(select(TextbookTopicDocument).where(TextbookTopicDocument.document_version_id == version_id))
    assert link and link.role == "primary" and link.printed_start_page == "101"

    @contextmanager
    def worker_session():
        yield session
    monkeypatch.setattr(document_processing, "SessionLocal", worker_session)
    storage = app.dependency_overrides[get_storage](); queue = app.dependency_overrides[get_document_queue]()
    assert document_processing.process_job(uuid.UUID(upload.json()["job"]["id"]), storage) == "needs_review"
    extraction = client.get(f"/api/v1/documents/{upload.json()['document']['id']}/extraction").json()
    page = extraction["pages"][0]
    assert page["originalRenderAssetId"] and page["renderAssetId"] != page["originalRenderAssetId"]
    assert "contrastScore" in page["metadata"]
    block = page["blocks"][0]
    corrected = client.post(
        f"/api/v1/documents/{upload.json()['document']['id']}/extraction/blocks/{block['id']}", headers=headers,
        json={"kind": "equation", "text": "H2SO4 + NaOH → salt", "latex": "H_2SO_4", "sequenceNumber": block["sequenceNumber"]},
    )
    assert corrected.status_code == 200 and corrected.json()["pages"][0]["blocks"][0]["needsReview"] is False
    labelled = client.post(
        f"/api/v1/documents/{upload.json()['document']['id']}/extraction/pages/{page['id']}", headers=headers,
        json={"printedPageLabel": "101"},
    )
    assert labelled.status_code == 200 and labelled.json()["pages"][0]["printedPageLabel"] == "101"
    synchronized_document = client.get(f"/api/v1/documents/{upload.json()['document']['id']}")
    assert synchronized_document.status_code == 200
    assert synchronized_document.json()["status"] == "completed"
    session.refresh(link)
    assert link.review_status == "ready"
    stored_document = session.get(Document, uuid.UUID(upload.json()["document"]["id"]))
    assert stored_document.review_state == "reviewed"
    assert session.scalar(select(DocumentEvent).where(
        DocumentEvent.document_version_id == version_id,
        DocumentEvent.event_type == "extraction_review_completed",
    ))
    ready_book = client.get(f"/api/v1/admin/textbooks/{book_ref}").json()
    ready_topic = next(item for row in ready_book["groups"] for item in row["topics"] if item["topicRef"] == topic_ref)
    assert ready_topic["content"]["state"] == "ready" and ready_topic["content"]["ready"] is True
    confirmation = {"confirmSources": True, "confirmExtraction": True, "confirmTopic": True}
    published_content = client.post(f"/api/v1/admin/textbooks/{book_ref}/topics/{topic_ref}/publish",
                                    headers=headers, json=confirmation)
    assert published_content.status_code == 200, published_content.text
    published_topic = next(item for row in published_content.json()["groups"] for item in row["topics"] if item["topicRef"] == topic_ref)
    assert published_topic["content"]["state"] == "published" and published_topic["content"]["contentVersion"] == 1
    content_version = session.scalar(select(TextbookTopicContentVersion).where(
        TextbookTopicContentVersion.topic_id == link.topic_id, TextbookTopicContentVersion.status == "published"))
    assert content_version and content_version.source_manifest[0]["documentVersionId"] == str(version_id)
    assert session.query(RetrievalChunk).filter_by(topic_content_version_id=content_version.id, status="active").count() >= 1
    revised = client.post(
        f"/api/v1/documents/{upload.json()['document']['id']}/extraction/blocks/{block['id']}", headers=headers,
        json={"kind": "equation", "text": "H2SO4 + 2NaOH → Na2SO4 + 2H2O", "latex": "H_2SO_4 + 2NaOH",
              "sequenceNumber": block["sequenceNumber"]},
    )
    assert revised.status_code == 200
    reviewed_block = session.get(DocumentBlock, uuid.UUID(block["id"]))
    session.add(DocumentBlock(document_version_id=reviewed_block.document_version_id,
        page_id=reviewed_block.page_id, sequence_number=reviewed_block.sequence_number + 100,
        block_kind=reviewed_block.block_kind, text=reviewed_block.text, latex=reviewed_block.latex,
        bounding_box=reviewed_block.bounding_box, extraction_method=reviewed_block.extraction_method,
        confidence=reviewed_block.confidence, needs_review=False,
        source_asset_id=reviewed_block.source_asset_id, block_metadata={"testDuplicate": True}))
    session.commit()
    republished_content = client.post(f"/api/v1/admin/textbooks/{book_ref}/topics/{topic_ref}/publish",
                                      headers=headers, json=confirmation)
    assert republished_content.status_code == 200
    versions = session.scalars(select(TextbookTopicContentVersion).where(
        TextbookTopicContentVersion.topic_id == link.topic_id).order_by(TextbookTopicContentVersion.version_number)).all()
    assert [row.status for row in versions] == ["superseded", "published"]
    assert session.query(RetrievalChunk).filter_by(topic_content_version_id=versions[0].id, status="superseded").count() >= 1
    active_chunks = session.query(RetrievalChunk).filter_by(
        topic_content_version_id=versions[1].id, status="active").all()
    assert active_chunks and len({row.content_hash for row in active_chunks}) == len(active_chunks)
    unchanged = client.post(f"/api/v1/admin/textbooks/{book_ref}/topics/{topic_ref}/publish",
                            headers=headers, json=confirmation)
    assert unchanged.status_code == 409 and unchanged.json()["error"]["code"] == "topic_content_not_ready"

    # Step 5: publish cumulative topic coverage, clone it, append a newly covered topic,
    # and retain the assessment's original immutable snapshot.
    second_topic = session.scalar(select(TextbookTopic).where(
        TextbookTopic.textbook_id == textbook.id, TextbookTopic.id != link.topic_id,
    ))
    admin = session.query(User).filter_by(username=username).one()
    second_topic.status = "published"
    session.add(TextbookTopicContentVersion(topic_id=second_topic.id, version_number=1, status="published",
        source_manifest=[{"test": True}], extraction_manifest={"test": True}, published_by=admin.id))
    student_user = User(username=f"coverage-student-{uuid.uuid4().hex}", display_name="Coverage Student",
        role="student", password_hash=hash_password("coverage student password"), must_change_password=False)
    parent_user = User(username=f"coverage-parent-{uuid.uuid4().hex}", display_name="Coverage Parent",
        role="parent", password_hash=hash_password("coverage parent password"), must_change_password=False)
    session.add_all([parent_user, student_user]); session.flush()
    session.add_all([StudentProfile(student_id=student_user.id, parent_id=parent_user.id),
        StudentProgression(student_id=student_user.id, course_id="igcse", grade=10, term=1, is_current=True),
        StudentProgression(student_id=student_user.id, course_id="igcse", grade=10, term=2, is_current=False),
        StudentSubject(student_id=student_user.id, subject_id="chemistry")]); session.commit()
    initial_plan = client.get("/api/v1/admin/curriculum-plans/chemistry").json()
    assert initial_plan["status"] == "not_started" and initial_plan["groups"]
    draft = client.post("/api/v1/admin/curriculum-plans/chemistry/draft", headers=headers, json={}).json()
    draft["periods"][0]["topicRefs"] = [topic_ref]
    saved = client.post("/api/v1/admin/curriculum-plans/chemistry", headers=headers,
                        json={"periods": draft["periods"]})
    assert saved.status_code == 200
    first_publication = client.post("/api/v1/admin/curriculum-plans/chemistry/publish", headers=headers,
        json={"confirmSubject": True, "confirmTextbook": True})
    assert first_publication.status_code == 200
    frozen = snapshot(session, "topic-coverage-assessment", student_user.id, "chemistry")
    assert frozen.covered_topic_ids == [str(link.topic_id)]
    next_draft = client.post("/api/v1/admin/curriculum-plans/chemistry/draft", headers=headers, json={}).json()
    assert next_draft["basedOnVersion"] == 1 and next_draft["periods"][0]["topicRefs"] == [topic_ref]
    next_draft["periods"][1]["topicRefs"] = [second_topic.public_ref]
    revised_plan = client.post("/api/v1/admin/curriculum-plans/chemistry", headers=headers,
                               json={"periods": next_draft["periods"]}).json()
    assert revised_plan["changes"][0]["change"] == "added"
    assert client.post("/api/v1/admin/curriculum-plans/chemistry/publish", headers=headers,
        json={"confirmSubject": True, "confirmTextbook": True}).status_code == 200
    progression = session.query(StudentProgression).filter_by(student_id=student_user.id).all()
    next(row for row in progression if row.term == 1).is_current = False
    session.commit()
    next(row for row in progression if row.term == 2).is_current = True
    session.commit()
    cumulative = client.get(f"/api/v1/admin/students/{student_user.id}/coverage",
                            params={"subjectId": "chemistry"}).json()
    assert {row["topicRef"] for row in cumulative["coveredTopics"]} == {topic_ref, second_topic.public_ref}
    assert snapshot(session, "topic-coverage-assessment", student_user.id, "chemistry").covered_topic_ids == [str(link.topic_id)]
    destructive = client.post("/api/v1/admin/curriculum-plans/chemistry/draft", headers=headers, json={}).json()
    destructive["periods"][1]["topicRefs"] = []
    changed_plan = client.post("/api/v1/admin/curriculum-plans/chemistry", headers=headers,
                               json={"periods": destructive["periods"]}).json()
    assert changed_plan["requiresPublishedChangeConfirmation"] is True
    blocked = client.post("/api/v1/admin/curriculum-plans/chemistry/publish", headers=headers,
        json={"confirmSubject": True, "confirmTextbook": True})
    assert blocked.status_code == 409 and blocked.json()["error"]["code"] == "curriculum_published_change_confirmation_required"
    assert client.post("/api/v1/admin/curriculum-plans/chemistry/publish", headers=headers,
        json={"confirmSubject": True, "confirmTextbook": True, "confirmPublishedChanges": True}).status_code == 200
    assert session.query(CurriculumPlan).filter_by(subject_id="chemistry", status="superseded").count() == 2

    second_pdf = fitz.open(); second_page = second_pdf.new_page(); second_page.insert_text((72, 72), "Topic 11 acids")
    second_bytes = second_pdf.tobytes(); second_pdf.close()
    batch = client.post(f"/api/v1/admin/textbooks/{book_ref}/topics/{topic_ref}/documents/batch", headers=headers,
                        json={"items": [{"filename": "topic-11-part-2.pdf", "contentType": "application/pdf",
                                         "contentBase64": base64.b64encode(second_bytes).decode(), "role": "supporting",
                                         "idempotencyKey": "topic-11-second-part"}]})
    assert batch.status_code == 201 and batch.json()[0]["document"]["sourceMetadata"]["topicRef"] == topic_ref


@pytest.mark.integration
def test_topic_question_mapping_is_weighted_same_subject_and_requires_all_topics(auth_client) -> None:
    client, username, password = auth_client
    login = client.post("/api/v1/auth/login", json={"username": username, "password": password}).json()
    headers = {"X-CSRF-Token": login["csrfToken"]}; session = next(app.dependency_overrides[get_db]())
    admin = session.query(User).filter_by(username=username).one()
    book = Textbook(course_id="igcse", subject_id="chemistry", title="Mapping chemistry", edition="2026",
        publisher="Test", group_label="unit", status="published", created_by=admin.id, published_by=admin.id)
    foreign_book = Textbook(course_id="igcse", subject_id="biology", title="Mapping biology", edition="2026",
        publisher="Test", group_label="unit", status="published", created_by=admin.id, published_by=admin.id)
    session.add_all([book, foreign_book]); session.flush()
    groups = [TextbookGroup(textbook_id=book.id, code=f"U{i}", title=f"Unit {i}", sequence=i, status="published") for i in (1,2)]
    foreign_group = TextbookGroup(textbook_id=foreign_book.id, code="B1", title="Biology", sequence=1, status="published")
    session.add_all([*groups, foreign_group]); session.flush()
    topics = [TextbookTopic(textbook_id=book.id, group_id=groups[i].id, course_id="igcse", subject_id="chemistry",
        code=str(code), title=title, sequence=1, status="published") for i,(code,title) in enumerate(((4,"Acids"),(7,"Equations")))]
    foreign_topic = TextbookTopic(textbook_id=foreign_book.id, group_id=foreign_group.id, course_id="igcse",
        subject_id="biology", code="B1", title="Cells", sequence=1, status="published")
    session.add_all([*topics, foreign_topic]); session.flush()
    for topic in [*topics, foreign_topic]: session.add(TextbookTopicContentVersion(topic_id=topic.id, version_number=1,
        status="published", source_manifest=[{"test":True}], extraction_manifest={}, published_by=admin.id))
    paper = Document(kind="past_paper", course_id="igcse", subject_id="chemistry", title="Topic paper",
        original_filename="paper.pdf", object_key=f"test/{uuid.uuid4()}", mime_type="application/pdf",
        sha256=uuid.uuid4().hex*2, review_state="published", uploaded_by=admin.id, size_bytes=1)
    session.add(paper); session.flush()
    source = DocumentVersion(document_id=paper.id, version_number=1, original_filename="paper.pdf",
        object_key=f"test/{uuid.uuid4()}", mime_type="application/pdf", sha256=uuid.uuid4().hex*2,
        size_bytes=1, status="completed", uploaded_by=admin.id)
    session.add(source); session.flush()
    material = OfficialMaterialVersion(document_id=paper.id, source_document_version_id=source.id, version_number=1,
        kind="past_paper", course_id="igcse", subject_id="chemistry", textbook_id=book.id, status="published",
        inventory_count=1, completeness_confirmed=True, created_by=admin.id, published_by=admin.id)
    session.add(material); session.flush()
    question = OfficialQuestionVersion(material_version_id=material.id, question_number="1", prompt="Explain acids using an equation.",
        shared_stem="Use the reaction evidence.", marks=4, source_locations=[{"page":1,"blockId":"evidence","boundingBox":{}}])
    session.add(question); session.commit()
    inventory = client.get(f"/api/v1/questions/papers/{paper.id}/topic-mappings").json()
    assert len(inventory["groups"]) == 2 and inventory["questions"][0]["sourceLocations"][0]["page"] == 1
    foreign = client.post(f"/api/v1/questions/{question.id}/topic-mapping", headers=headers, json={"mappings":[
        {"topicRef":foreign_topic.public_ref,"weight":100,"required":True}]})
    assert foreign.status_code == 422 and foreign.json()["error"]["code"] == "foreign_topic_mapping"
    saved = client.post(f"/api/v1/questions/{question.id}/topic-mapping", headers=headers, json={"mappings":[
        {"topicRef":topics[0].public_ref,"weight":60,"required":True},
        {"topicRef":topics[1].public_ref,"weight":40,"required":True}]})
    assert saved.status_code == 200 and saved.json()["groupWeights"] == {"U1":60,"U2":40}
    assert client.post(f"/api/v1/questions/{question.id}/topic-mapping/publish", headers=headers, json={}).status_code == 200
    rows = session.query(OfficialQuestionTopicMapping).filter_by(question_version_id=question.id, status="confirmed").all()
    assert len(rows) == 2 and all(row.required for row in rows)
    parent = User(username=f"mapping-parent-{uuid.uuid4().hex}", display_name="Mapping Parent", role="parent",
        password_hash=hash_password("mapping parent password"), must_change_password=False)
    student = User(username=f"mapping-student-{uuid.uuid4().hex}", display_name="Mapping Student", role="student",
        password_hash=hash_password("mapping student password"), must_change_password=False)
    session.add_all([parent, student]); session.flush()
    session.add_all([StudentProfile(student_id=student.id, parent_id=parent.id),
        StudentProgression(student_id=student.id, course_id="igcse", grade=10, term=1, is_current=True),
        StudentSubject(student_id=student.id, subject_id="chemistry")])
    plan = CurriculumPlan(course_id="igcse", subject_id="chemistry", textbook_id=book.id,
        version_number=1, status="published", created_by=admin.id, published_by=admin.id)
    session.add(plan); session.flush()
    session.add(CurriculumPlanTopic(plan_id=plan.id, grade=10, term=1, topic_id=topics[0].id)); session.commit()
    assert assessments.eligible_questions(session, student.id, "chemistry") == []
    session.add(CurriculumPlanTopic(plan_id=plan.id, grade=10, term=1, topic_id=topics[1].id)); session.commit()
    assert [row[0].id for row in assessments.eligible_questions(session, student.id, "chemistry")] == [question.id]


@pytest.mark.integration
def test_admin_manages_openai_account_priorities_without_exposing_secrets(auth_client) -> None:
    client, username, password = auth_client
    assert client.get("/api/v1/admin/ai-accounts").status_code == 401
    login = client.post("/api/v1/auth/login", json={"username": username, "password": password}).json()
    headers = {"X-CSRF-Token": login["csrfToken"]}
    created = client.post("/api/v1/admin/ai-accounts", headers=headers, json={
        "name": "Primary project", "credentialAlias": "PRIMARY_TEST",
        "priority": 7, "model": "test-model", "enabled": True,
    })
    assert created.status_code == 201
    assert created.json() == {
        "name": "Primary project", "credentialAlias": "PRIMARY_TEST", "priority": 7,
        "model": "test-model", "enabled": True, "credentialConfigured": False,
        "healthStatus": "unknown", "cooldownUntil": None, "lastErrorCode": None,
        "lastSuccessAt": None, "lastFailureAt": None,
    }
    assert "key" not in str(created.json()).lower()
    conflict = client.post("/api/v1/admin/ai-accounts", headers=headers, json={
        "name": "Backup project", "credentialAlias": "BACKUP_TEST",
        "priority": 7, "model": "test-model", "enabled": True,
    })
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "ai_account_conflict"
    updated = client.post("/api/v1/admin/ai-accounts/PRIMARY_TEST", headers=headers, json={
        "name": "Primary project", "credentialAlias": "PRIMARY_TEST",
        "priority": 2, "model": "test-model", "enabled": False,
    })
    assert updated.status_code == 200
    listed = client.get("/api/v1/admin/ai-accounts")
    assert listed.status_code == 200
    assert any(row["priority"] == 2 and not row["enabled"] for row in listed.json())


@pytest.mark.integration
def test_admin_creates_parent_and_student_with_scoped_state(auth_client) -> None:
    client, admin_username, admin_password = auth_client
    login = client.post("/api/v1/auth/login", json={"username": admin_username, "password": admin_password}).json()
    headers = {"X-CSRF-Token": login["csrfToken"]}

    invalid_parent = client.post("/api/v1/admin/accounts", headers=headers, json={
        "username": "short-password-parent", "name": "Test Parent",
        "password": "too-short", "role": "parent",
    })
    assert invalid_parent.status_code == 422
    assert any(
        issue["location"][-1] == "password" and "at least 12 characters" in issue["message"]
        for issue in invalid_parent.json()["error"]["details"]
    )

    parent_username = f"parent-{uuid.uuid4().hex[:12]}"
    parent_password = "temporary parent password"
    parent_response = client.post("/api/v1/admin/accounts", headers=headers, json={
        "username": parent_username, "name": "Test Parent", "password": parent_password, "role": "parent",
    })
    assert parent_response.status_code == 201
    parent = parent_response.json()

    student_username = f"student-{uuid.uuid4().hex[:12]}"
    student_password = "temporary student password"
    student_response = client.post("/api/v1/admin/accounts", headers=headers, json={
        "username": student_username, "name": "Test Student", "password": student_password,
        "role": "student", "parentId": parent["id"], "level": "iGCSE",
        "grade": "Grade 10", "term": "Term2",
        "progression": ["Grade 10|Term1", "Grade 10|Term2"],
        "subjects": ["maths", "physics"],
    })
    assert student_response.status_code == 201
    student = student_response.json()

    state = client.get("/api/v1/state").json()
    assert {account["username"] for account in state["accounts"]} >= {parent_username, student_username}
    student_state = next(row for row in state["students"] if row["id"] == student["id"])
    assert student_state["parentId"] == parent["id"]
    assert student_state["grade"] == "Grade 10"
    assert student_state["term"] == "Term2"
    assert student_state["progression"] == [
        {"grade": "Grade 10", "term": "Term1"},
        {"grade": "Grade 10", "term": "Term2"},
    ]
    assert set(student_state["subjects"]) == {"maths", "physics"}

    session: Session = next(app.dependency_overrides[get_db]())
    assert session.get(StudentProfile, uuid.UUID(student["id"])).parent_id == uuid.UUID(parent["id"])
    assert len(session.query(StudentProgression).filter_by(student_id=uuid.UUID(student["id"])).all()) == 2
    assert len(session.query(StudentSubject).filter_by(student_id=uuid.UUID(student["id"])).all()) == 2
    assert session.query(AuditEvent).filter_by(target_id=student["id"], action="account.created").count() == 1

    parent_login = client.post("/api/v1/auth/login", json={"username": parent_username, "password": parent_password}).json()
    assert parent_login["user"]["mustChangePassword"] is True
    parent_state = client.get("/api/v1/state").json()
    assert parent_state["accounts"] == []
    assert parent_state["students"] == []
    assert client.get("/api/v1/admin/ui-features").status_code == 403
    parent_headers = {"X-CSRF-Token": parent_login["csrfToken"]}
    blocked_until_changed = client.post("/api/v1/admin/accounts", headers=parent_headers, json={
        "username": "forbidden-user", "name": "Forbidden", "password": "a secure temporary password", "role": "parent",
    })
    assert blocked_until_changed.status_code == 403

    changed = client.post("/api/v1/auth/change-password", headers=parent_headers, json={
        "newPassword": "parent chose a new secure password",
    })
    assert changed.status_code == 204
    parent_state = client.get("/api/v1/state").json()
    assert [row["id"] for row in parent_state["students"]] == [student["id"]]
    forbidden = client.post("/api/v1/admin/accounts", headers=parent_headers, json={
        "username": "still-forbidden", "name": "Forbidden", "password": "a secure temporary password", "role": "parent",
    })
    assert forbidden.status_code == 403


@pytest.mark.integration
def test_new_user_changes_temporary_password(auth_client) -> None:
    client, admin_username, admin_password = auth_client
    login = client.post("/api/v1/auth/login", json={"username": admin_username, "password": admin_password}).json()
    initial_password = "temporary secure password"
    username = f"parent-{uuid.uuid4().hex[:12]}"
    client.post("/api/v1/admin/accounts", headers={"X-CSRF-Token": login["csrfToken"]}, json={
        "username": username, "name": "Password Parent", "password": initial_password, "role": "parent",
    })
    user_login = client.post("/api/v1/auth/login", json={"username": username, "password": initial_password}).json()
    reused = client.post("/api/v1/auth/change-password", headers={"X-CSRF-Token": user_login["csrfToken"]}, json={
        "newPassword": initial_password,
    })
    assert reused.status_code == 400
    assert reused.json()["error"] == {
        "code": "password_reused",
        "message": "The new password cannot be same as the existing password.",
        "details": [],
    }
    response = client.post("/api/v1/auth/change-password", headers={"X-CSRF-Token": user_login["csrfToken"]}, json={
        "newPassword": "a completely new secure password",
    })
    assert response.status_code == 204
    assert client.get("/api/v1/auth/me").json()["mustChangePassword"] is False


@pytest.mark.integration
def test_admin_reset_one_time_disclosure_session_revocation_and_known_change(auth_client) -> None:
    admin_client, admin_username, admin_password = auth_client
    admin_login = admin_client.post("/api/v1/auth/login", json={
        "username": admin_username, "password": admin_password}).json()
    admin_headers = {"X-CSRF-Token": admin_login["csrfToken"]}
    username = f"reset-parent-{uuid.uuid4().hex[:12]}"
    original = "original secure password"
    created = admin_client.post("/api/v1/admin/accounts", headers=admin_headers, json={
        "username": username, "name": "Reset Parent", "password": original, "role": "parent",
    })
    assert created.status_code == 201
    assert created.json()["publicRef"].startswith("account_")

    target_client = TestClient(app, base_url="http://localhost")
    first_login = target_client.post("/api/v1/auth/login", json={
        "username": username, "password": original}).json()
    assert first_login["user"]["mustChangePassword"] is True
    request_key = f"reset-{uuid.uuid4().hex}"
    reset = admin_client.post(
        f"/api/v1/admin/accounts/{created.json()['publicRef']}/reset-password",
        headers=admin_headers, json={"requestKey": request_key})
    assert reset.status_code == 200
    temporary = reset.json()["temporaryPassword"]
    assert len(temporary) == 20 and reset.headers["cache-control"] == "no-store"
    assert reset.json()["sessionsRevoked"] == 1
    assert target_client.get("/api/v1/auth/me").status_code == 401
    assert admin_client.post(
        f"/api/v1/admin/accounts/{created.json()['publicRef']}/reset-password",
        headers=admin_headers, json={"requestKey": request_key}).status_code == 409
    assert target_client.post("/api/v1/auth/login", json={
        "username": username, "password": original}).status_code == 401

    temporary_login = target_client.post("/api/v1/auth/login", json={
        "username": username, "password": temporary}).json()
    replacement = "replacement secure password"
    changed = target_client.post("/api/v1/auth/change-password",
        headers={"X-CSRF-Token": temporary_login["csrfToken"]},
        json={"newPassword": replacement})
    assert changed.status_code == 204
    assert target_client.get("/api/v1/auth/me").json()["mustChangePassword"] is False
    assert target_client.post("/api/v1/auth/login", json={
        "username": username, "password": temporary}).status_code == 401

    second_device = TestClient(app, base_url="http://localhost")
    assert second_device.post("/api/v1/auth/login", json={
        "username": username, "password": replacement}).status_code == 200
    csrf = target_client.cookies.get("akuru_csrf")
    rejected = target_client.post("/api/v1/auth/change-known-password",
        headers={"X-CSRF-Token": csrf}, json={
            "currentPassword": "incorrect current password", "newPassword": "another secure password"})
    assert rejected.status_code == 400
    final_password = "final secure password"
    normal = target_client.post("/api/v1/auth/change-known-password",
        headers={"X-CSRF-Token": csrf}, json={
            "currentPassword": replacement, "newPassword": final_password})
    assert normal.status_code == 204
    assert target_client.get("/api/v1/auth/me").status_code == 200
    assert second_device.get("/api/v1/auth/me").status_code == 401
    assert target_client.post(
        f"/api/v1/admin/accounts/{created.json()['publicRef']}/reset-password",
        headers={"X-CSRF-Token": target_client.cookies.get("akuru_csrf")},
        json={"requestKey": f"forbidden-{uuid.uuid4().hex}"}).status_code == 403

    session: Session = next(app.dependency_overrides[get_db]())
    user = session.scalar(select(User).where(User.username == username))
    assert user.last_login_at is not None
    assert session.query(AuthSession).filter_by(user_id=user.id).count() == 1
    assert session.query(PasswordResetReceipt).filter_by(request_key=request_key).count() == 1
    events = session.scalars(select(AuditEvent).where(AuditEvent.target_id == user.public_ref)).all()
    serialized = json.dumps([event.event_data for event in events])
    assert temporary not in serialized and replacement not in serialized and final_password not in serialized
    security_events = admin_client.get("/api/v1/admin/accounts/security-events")
    assert security_events.status_code == 200
    assert any(event["action"] == "account.password_reset" and
               event["targetRef"] == user.public_ref for event in security_events.json())


@pytest.mark.integration
def test_tutor_profiles_are_versioned_role_scoped_and_use_curated_presets(auth_client) -> None:
    client, admin_username, admin_password = auth_client
    session: Session = next(app.dependency_overrides[get_db]())
    parent = User(username=f"tutor-parent-{uuid.uuid4().hex}", display_name="Tutor Parent", role="parent",
                  password_hash=hash_password("tutor parent password"), must_change_password=False)
    other_parent = User(username=f"tutor-other-parent-{uuid.uuid4().hex}", display_name="Other Parent", role="parent",
                        password_hash=hash_password("other tutor parent password"), must_change_password=False)
    student = User(username=f"tutor-student-{uuid.uuid4().hex}", display_name="Tutor Student", role="student",
                   password_hash=hash_password("tutor student password"), must_change_password=False)
    sibling = User(username=f"tutor-sibling-{uuid.uuid4().hex}", display_name="Tutor Sibling", role="student",
                   password_hash=hash_password("tutor sibling password"), must_change_password=False)
    session.add_all([parent, other_parent, student, sibling]); session.flush()
    session.add_all([
        StudentProfile(student_id=student.id, parent_id=parent.id),
        StudentProfile(student_id=sibling.id, parent_id=other_parent.id),
    ]); session.commit()

    assert client.get("/api/v1/tutoring/options").status_code == 401
    student_login = client.post("/api/v1/auth/login", json={
        "username": student.username, "password": "tutor student password",
    }).json()
    student_headers = {"X-CSRF-Token": student_login["csrfToken"]}
    options = client.get("/api/v1/tutoring/options")
    assert options.status_code == 200
    assert len(options.json()["avatars"]) == 5 and len(options.json()["voices"]) == 5
    assert "providerVoice" not in options.text and '"id"' not in options.text
    assert all(row["enabled"] is True and "sortOrder" not in row for row in options.json()["avatars"])
    assert options.json()["communicationCharacters"] == ["childlike", "balanced", "authoritative"]

    first_payload = {
        "name": "Spark Tutor", "presentation": "neutral", "avatarCode": "akuru-spark",
        "voiceCode": "bright-companion", "tone": "encouraging", "friendliness": "high",
        "enthusiasm": "medium", "speed": "medium", "communicationCharacter": "balanced",
        "explanationDepth": "standard", "teachingStyle": "guided",
    }
    invalid_name = client.post("/api/v1/tutoring/profiles", headers=student_headers,
                               json={**first_payload, "name": "<script>"})
    assert invalid_name.status_code == 422
    assert client.post("/api/v1/tutoring/profiles", json=first_payload).status_code == 403
    created = client.post("/api/v1/tutoring/profiles", headers=student_headers, json=first_payload)
    assert created.status_code == 201, created.text
    profile = created.json()
    assert profile["profileRef"].startswith("tutor_") and profile["version"] == 1
    assert "id" not in profile and "studentId" not in profile

    renamed_payload = {
        **first_payload, "name": "Atlas Algebra", "presentation": "masculine",
        "avatarCode": "akuru-atlas", "voiceCode": "clear-coach", "tone": "direct",
        "communicationCharacter": "authoritative", "teachingStyle": "example_led",
    }
    renamed = client.post(f"/api/v1/tutoring/profiles/{profile['profileRef']}",
                          headers=student_headers, json=renamed_payload)
    assert renamed.status_code == 200 and renamed.json()["version"] == 2
    assert renamed.json()["name"] == "Atlas Algebra"
    database_profile = session.scalar(select(TutorProfile).where(TutorProfile.public_ref == profile["profileRef"]))
    assert database_profile and database_profile.current_version_number == 2
    versions = session.scalars(select(TutorProfileVersion).where(
        TutorProfileVersion.profile_id == database_profile.id).order_by(TutorProfileVersion.version_number)).all()
    assert [row.name for row in versions] == ["Spark Tutor", "Atlas Algebra"]

    client.post("/api/v1/auth/logout", headers=student_headers)
    sibling_login = client.post("/api/v1/auth/login", json={
        "username": sibling.username, "password": "tutor sibling password",
    }).json()
    sibling_headers = {"X-CSRF-Token": sibling_login["csrfToken"]}
    assert client.post(f"/api/v1/tutoring/profiles/{profile['profileRef']}",
                       headers=sibling_headers, json=first_payload).status_code == 404

    client.post("/api/v1/auth/logout", headers=sibling_headers)
    parent_login = client.post("/api/v1/auth/login", json={
        "username": parent.username, "password": "tutor parent password",
    }).json()
    own_profiles = client.get(f"/api/v1/tutoring/students/{student.id}/profiles")
    assert own_profiles.status_code == 200 and own_profiles.json()["profiles"][0]["name"] == "Atlas Algebra"
    client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": parent_login["csrfToken"]})

    other_login = client.post("/api/v1/auth/login", json={
        "username": other_parent.username, "password": "other tutor parent password",
    }).json()
    assert client.get(f"/api/v1/tutoring/students/{student.id}/profiles").status_code == 404
    client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": other_login["csrfToken"]})

    admin_login = client.post("/api/v1/auth/login", json={
        "username": admin_username, "password": admin_password,
    }).json()
    admin_headers = {"X-CSRF-Token": admin_login["csrfToken"]}
    assert client.post("/api/v1/tutoring/profiles", headers=admin_headers, json=first_payload).status_code == 403
    presets = client.get("/api/v1/tutoring/admin/presets")
    assert presets.status_code == 200 and "provider_voice_ref" not in presets.text
    disabled = client.post("/api/v1/tutoring/admin/avatars/akuru-spark", headers=admin_headers,
                           json={"enabled": False, "sortOrder": 99})
    assert disabled.status_code == 200
    spark = next(row for row in disabled.json()["avatars"] if row["code"] == "akuru-spark")
    assert spark["enabled"] is False and spark["sortOrder"] == 99

    client.post("/api/v1/auth/logout", headers=admin_headers)
    student_login = client.post("/api/v1/auth/login", json={
        "username": student.username, "password": "tutor student password",
    }).json()
    student_headers = {"X-CSRF-Token": student_login["csrfToken"]}
    assert client.post("/api/v1/tutoring/profiles", headers=student_headers,
                       json=first_payload).json()["error"]["code"] == "tutor_avatar_unavailable"
    removed = client.delete(f"/api/v1/tutoring/profiles/{profile['profileRef']}", headers=student_headers)
    assert removed.status_code == 204
    assert client.get("/api/v1/tutoring/profiles").json() == {"profiles": []}
    assert session.query(TutorProfileVersion).filter_by(profile_id=database_profile.id).count() == 2


@pytest.mark.integration
def test_admin_document_upload_validation_private_download_and_removal(auth_client, monkeypatch) -> None:
    client, username, password = auth_client
    assert client.get("/api/v1/documents").status_code == 401
    login = client.post("/api/v1/auth/login", json={"username": username, "password": password}).json()
    headers = {
        "X-CSRF-Token": login["csrfToken"],
        "X-Filename": "biology-textbook.pdf",
        "Content-Type": "application/pdf",
    }
    params = {
        "kind": "textbook",
        "courseId": "igcse",
        "subjectId": "biology",
        "title": "Biology Student Book",
        "edition": "Second edition",
        "year": 2025,
        "publisher": "Test Publisher",
    }
    fixture = fitz.open()
    fixture_page = fixture.new_page()
    fixture_page.insert_text((72, 72), "BIOLOGY", fontsize=20)
    fixture_page.insert_text((72, 120), "1. Explain how cells exchange materials.", fontsize=12)
    content = fixture.tobytes()
    fixture.close()
    uploaded = client.post("/api/v1/documents", params=params, headers=headers, content=content)
    assert uploaded.status_code == 201, uploaded.text
    upload_payload = uploaded.json()
    document = upload_payload["document"]
    job_payload = upload_payload["job"]
    assert document["kind"] == "textbook"
    assert document["subjectId"] == "biology"
    assert document["sourceMetadata"] == {"publisher": "Test Publisher"}
    assert document["sizeBytes"] == len(content)
    assert document["status"] == "queued"
    assert job_payload["status"] == "queued"
    queue = app.dependency_overrides[get_document_queue]()
    assert queue.job_ids == [uuid.UUID(job_payload["id"])]

    listed = client.get("/api/v1/documents").json()["documents"]
    assert [row["id"] for row in listed] == [document["id"]]
    downloaded = client.get(f"/api/v1/documents/{document['id']}/content")
    assert downloaded.status_code == 200
    assert downloaded.content == content
    assert "biology-textbook.pdf" in downloaded.headers["content-disposition"]
    assert downloaded.headers["cache-control"] == "private, no-store"

    duplicate = client.post("/api/v1/documents", params=params, headers=headers, content=content)
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "duplicate_document"

    wrong_signature = client.post(
        "/api/v1/documents",
        params={**params, "title": "Not really a PDF"},
        headers={**headers, "X-Filename": "not-a-pdf.pdf"},
        content=b"this is not a PDF",
    )
    assert wrong_signature.status_code == 422
    assert wrong_signature.json()["error"]["code"] == "file_signature_mismatch"

    parent_username = f"document-parent-{uuid.uuid4().hex[:10]}"
    temporary_password = "temporary document parent password"
    parent = client.post("/api/v1/admin/accounts", headers={"X-CSRF-Token": login["csrfToken"]}, json={
        "username": parent_username,
        "name": "Document Test Parent",
        "password": temporary_password,
        "role": "parent",
    })
    assert parent.status_code == 201
    with TestClient(app, base_url="http://localhost") as parent_client:
        parent_login = parent_client.post("/api/v1/auth/login", json={
            "username": parent_username, "password": temporary_password,
        }).json()
        changed = parent_client.post(
            "/api/v1/auth/change-password",
            headers={"X-CSRF-Token": parent_login["csrfToken"]},
            json={"newPassword": "parent private document password"},
        )
        assert changed.status_code == 204
        assert parent_client.get(f"/api/v1/documents/{document['id']}/content").status_code == 403
        assert parent_client.get(f"/api/v1/documents/{document['id']}/extraction").status_code == 403

    session: Session = next(app.dependency_overrides[get_db]())
    stored_document = session.get(Document, uuid.UUID(document["id"]))
    stored_version = session.get(DocumentVersion, uuid.UUID(document["versionId"]))
    stored_job = session.get(DocumentJob, uuid.UUID(job_payload["id"]))
    assert stored_document.sha256 == document["checksum"]
    assert stored_version.object_key == stored_document.object_key
    assert session.query(DocumentEvent).filter_by(document_id=stored_document.id, event_type="queued").count() == 1

    retry_not_failed = client.post(
        f"/api/v1/documents/{document['id']}/retry",
        headers={"X-CSRF-Token": login["csrfToken"]},
    )
    assert retry_not_failed.status_code == 409
    stored_version.status = "failed"
    stored_job.status = "failed"
    stored_job.error_code = "test_failure"
    stored_job.error_message = "Synthetic retry test."
    stored_job.max_seconds = 5
    stored_job.max_memory_mb = 128
    stored_job.max_pages = 1
    session.commit()
    retried = client.post(
        f"/api/v1/documents/{document['id']}/retry",
        headers={"X-CSRF-Token": login["csrfToken"]},
    )
    assert retried.status_code == 200
    assert retried.json()["status"] == "queued"
    session.refresh(stored_job)
    processing_settings = get_settings()
    assert stored_job.max_seconds == processing_settings.document_job_timeout_seconds
    assert stored_job.max_memory_mb == processing_settings.document_job_memory_mb
    assert stored_job.max_pages == processing_settings.document_max_pages
    assert session.query(DocumentEvent).filter_by(
        document_id=stored_document.id, event_type="retry_queued"
    ).count() == 1

    @contextmanager
    def worker_session():
        yield session

    monkeypatch.setattr(document_processing, "SessionLocal", worker_session)
    storage = app.dependency_overrides[get_storage]()
    outcome = document_processing.process_job(stored_job.id, storage)
    assert outcome == "needs_review", (
        stored_job.error_code,
        stored_job.error_message,
    )
    status_response = client.get(f"/api/v1/documents/{document['id']}/jobs/latest")
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "needs_review"
    assert status_response.json()["progress"] == 100
    assert status_response.json()["result"]["pageCount"] == 1
    extraction = client.get(f"/api/v1/documents/{document['id']}/extraction")
    assert extraction.status_code == 200
    extracted_page = extraction.json()["pages"][0]
    assert extracted_page["pageNumber"] == 1
    assert extracted_page["blocks"]
    render = client.get(
        f"/api/v1/documents/{document['id']}/assets/{extracted_page['renderAssetId']}/content"
    )
    assert render.status_code == 200
    assert render.headers["content-type"] == "image/png"
    assert render.headers["cache-control"] == "private, no-store"
    assert session.query(DocumentPage).filter_by(document_version_id=stored_version.id).count() == 1
    assert session.query(DocumentBlock).filter_by(document_version_id=stored_version.id).count() >= 1
    assert session.query(DocumentAsset).filter_by(document_version_id=stored_version.id).count() >= 1
    assert session.query(DocumentEvent).filter_by(
        document_id=stored_document.id, event_type="extraction_completed"
    ).count() == 1
    assert status_response.json()["result"]["blockCount"] >= 2
    assert session.query(DocumentBlock).filter_by(document_version_id=stored_version.id).count() >= 2
    assert session.query(DocumentAsset).filter_by(
        document_version_id=stored_version.id, asset_kind="page_render"
    ).count() == 1

    attempts = stored_job.attempt_count
    extraction_counts = (
        session.query(DocumentPage).filter_by(document_version_id=stored_version.id).count(),
        session.query(DocumentBlock).filter_by(document_version_id=stored_version.id).count(),
        session.query(DocumentAsset).filter_by(document_version_id=stored_version.id).count(),
    )
    stored_job.status = "queued"
    stored_version.status = "queued"
    session.commit()
    assert document_processing.process_job(stored_job.id, storage) == "idempotent"
    assert stored_job.attempt_count == attempts
    assert extraction_counts == (
        session.query(DocumentPage).filter_by(document_version_id=stored_version.id).count(),
        session.query(DocumentBlock).filter_by(document_version_id=stored_version.id).count(),
        session.query(DocumentAsset).filter_by(document_version_id=stored_version.id).count(),
    )

    removed = client.delete(
        f"/api/v1/documents/{document['id']}",
        headers={"X-CSRF-Token": login["csrfToken"]},
    )
    assert removed.status_code == 204
    assert client.get(f"/api/v1/documents/{document['id']}/content").status_code == 404
    assert session.query(DocumentEvent).filter_by(document_id=stored_document.id, event_type="removed").count() == 1


@pytest.mark.integration
def test_admin_evaluation_corpus_regression_and_release_gate(auth_client) -> None:
    client, username, password = auth_client
    assert client.get("/api/v1/evaluations/admin").status_code == 401
    login = client.post("/api/v1/auth/login", json={"username": username, "password": password}).json()
    headers = {"X-CSRF-Token": login["csrfToken"]}
    cases = [
        {"caseId": "inventory", "category": "inventory", "expected": {"questionIds": ["Q1"]}},
        {"caseId": "ocr", "category": "ocr", "expected": {"text": "source text"}},
        {"caseId": "equation", "category": "equation", "expected": {"equation": "x^2"}},
        {"caseId": "diagram", "category": "diagram", "expected": {"preserved": True}},
        {"caseId": "mapping", "category": "mapping", "expected": {"topicRefs": ["topic_1"], "crossSubjectRejected": True}},
        {"caseId": "citation", "category": "topic_citation", "expected": {"topicIsolation": True, "requiredCitationFields": ["topicRef", "printedPage"]}},
        {"caseId": "marking", "category": "marking", "expected": {"marks": 2, "methodPoints": ["M1"]}},
        {"caseId": "feedback", "category": "feedback", "expected": {"smallErrors": ["unit"], "improvedAnswerRequired": True, "sourceIds": ["s1"]}},
        {"caseId": "repeat", "category": "repeatability", "expected": {"stableDecisions": ["M1"]}},
    ]
    created = client.post("/api/v1/evaluations/admin/corpora", headers=headers, json={"subjectId": "maths", "name": "Maths reviewed v1", "cases": cases})
    assert created.status_code == 201, created.text
    corpus_id = created.json()["id"]
    approved = client.post(f"/api/v1/evaluations/admin/corpora/{corpus_id}/review", headers=headers, json={"decision": "approved"})
    assert approved.status_code == 200 and approved.json()["status"] == "approved"
    outputs = {
        "inventory": {"questionIds": ["Q1"]}, "ocr": {"text": "source text"}, "equation": {"equation": "x^2"},
        "diagram": {"preserved": True}, "mapping": {"topicRefs": ["topic_1"], "crossSubjectRejected": True},
        "citation": {"topicIsolation": True, "citationFields": ["topicRef", "printedPage"]},
        "marking": {"marks": 2, "methodPoints": ["M1"]},
        "feedback": {"smallErrors": ["unit"], "improvedAnswer": "Use the correct unit.", "sourceIds": ["s1"]},
        "repeat": {"stableDecisions": ["M1"]},
    }
    run = client.post("/api/v1/evaluations/admin/runs", headers=headers, json={"corpusId": corpus_id, "candidateModel": "test-model", "promptVersion": "assessment-test-v1", "observations": [{"caseId": key, "output": value} for key, value in outputs.items()]})
    assert run.status_code == 201, run.text
    assert run.json()["passed"] is True and set(run.json()["metrics"]) == set(run.json()["thresholds"])
    blocked = client.post("/api/v1/evaluations/admin/releases", headers=headers, json={"subjectId": "physics", "workflow": "assessment_feedback", "mode": "automatic", "runId": run.json()["id"]})
    assert blocked.status_code == 409
    released = client.post("/api/v1/evaluations/admin/releases", headers=headers, json={"subjectId": "maths", "workflow": "assessment_feedback", "mode": "automatic", "runId": run.json()["id"], "confidenceThreshold": .85})
    assert released.status_code == 200 and released.json()["mode"] == "automatic"
    dashboard = client.get("/api/v1/evaluations/admin").json()
    assert "maths" not in dashboard["missingApprovedSubjects"]
    assert dashboard["runs"][0]["passed"] is True
    presets = client.get("/api/v1/tutoring/admin/presets").json()
    tutor_cases = [
        {"caseId":"tf","category":"tutor_factual","input":{"masteryLevel":"low"},"expected":{"requiredChecks":["fact"]}},
        {"caseId":"tm","category":"tutor_mathematical","input":{"masteryLevel":"medium"},"expected":{"requiredChecks":["math"]}},
        {"caseId":"tg","category":"tutor_grounding","input":{"masteryLevel":"high"},"expected":{"requiredChecks":["edition","page","reject-invented"]}},
        {"caseId":"tp","category":"tutor_personalisation","input":{"masteryLevel":"low"},"expected":{"requiredChecks":["claims","counts","confidence"]}},
        {"caseId":"tr","category":"tutor_recommendation","input":{"masteryLevel":"medium"},"expected":{"requiredChecks":["ranking"]}},
        {"caseId":"tpersona","category":"tutor_persona","input":{"masteryLevel":"high"},"expected":{"personaMatrixComplete":True,"personaCombinationCount":11664,"requiredChecks":["matrix","age","academic"]}},
        {"caseId":"ts","category":"tutor_security","input":{"masteryLevel":"low"},"expected":{"requiredChecks":["injection","cross-subject","sibling","unsupported-unit","formal"]}},
        {"caseId":"th","category":"tutor_handover","input":{"masteryLevel":"medium"},"expected":{"requiredChecks":["handover","student-isolation"]}},
        {"caseId":"tv","category":"tutor_voice","input":{"masteryLevel":"high"},"expected":{"requiredChecks":["french","captions","interrupt","latency","reconnect","quota"]}},
        {"caseId":"tps","category":"tutor_preset_safety","input":{"masteryLevel":"medium"},"expected":{"reviewedAvatarCodes":[x["code"] for x in presets["avatars"] if x["enabled"]],"reviewedVoiceCodes":[x["code"] for x in presets["voices"] if x["enabled"]],"requiredChecks":["avatars","voices","brand"]}},
        {"caseId":"to","category":"tutor_operations","input":{"masteryLevel":"low"},"expected":{"requiredChecks":["security","privacy","accessibility","cost","retention","rollback"]}},
    ]
    tutor_corpus = client.post("/api/v1/evaluations/admin/corpora", headers=headers,
        json={"subjectId":"maths","workflow":"tutor","name":"Tutor maths reviewed v1","cases":tutor_cases})
    assert tutor_corpus.status_code == 201, tutor_corpus.text
    tutor_approved = client.post(f"/api/v1/evaluations/admin/corpora/{tutor_corpus.json()['id']}/review",
        headers=headers, json={"decision":"approved"})
    assert tutor_approved.status_code == 200, tutor_approved.text
    observations = [{"caseId":case["caseId"],"output":{"passedChecks":case["expected"]["requiredChecks"]}} for case in tutor_cases]
    tutor_run = client.post("/api/v1/evaluations/admin/runs", headers=headers, json={"corpusId":tutor_corpus.json()["id"],
        "candidateModel":"tutor-model","promptVersion":"tutor-v1","modality":"text","environment":"staging","observations":observations})
    assert tutor_run.status_code == 201 and tutor_run.json()["passed"] is True, tutor_run.text
    skipped = client.post("/api/v1/evaluations/admin/releases", headers=headers, json={"subjectId":"maths","workflow":"tutor_text","mode":"automatic","runId":tutor_run.json()["id"],"audience":"students"})
    assert skipped.status_code == 409 and skipped.json()["error"]["code"] == "tutor_release_stage_invalid"
    for audience in ("admin_testing", "parent_pilot", "students"):
        staged = client.post("/api/v1/evaluations/admin/releases", headers=headers, json={"subjectId":"maths","workflow":"tutor_text","mode":"automatic","runId":tutor_run.json()["id"],"audience":audience})
        assert staged.status_code == 200 and staged.json()["audience"] == audience
    mismatch = client.post("/api/v1/evaluations/admin/releases", headers=headers, json={"subjectId":"maths","workflow":"tutor_voice","mode":"automatic","runId":tutor_run.json()["id"],"audience":"admin_testing"})
    assert mismatch.status_code == 409 and mismatch.json()["error"]["code"] == "tutor_release_modality_mismatch"
    dashboard = client.get("/api/v1/evaluations/admin").json()
    assert "maths" not in dashboard["missingApprovedTutorSubjects"]
    assert client.post("/api/v1/evaluations/admin/corpora", json={"subjectId": "maths", "name": "Denied", "cases": cases}).status_code == 403


@pytest.mark.integration
def test_per_child_tutor_quotas_are_admin_controlled_and_independent(auth_client) -> None:
    client, admin_username, admin_password = auth_client
    admin_login = client.post("/api/v1/auth/login", json={"username": admin_username, "password": admin_password}).json()
    admin_headers = {"X-CSRF-Token": admin_login["csrfToken"]}
    suffix = uuid.uuid4().hex[:10]
    parent = client.post("/api/v1/admin/accounts", headers=admin_headers, json={
        "username": f"quota-parent-{suffix}", "name": "Quota Parent",
        "password": "temporary parent quota password", "role": "parent",
    }).json()
    first, first_password = _create_quota_test_student(client, admin_headers, parent["id"], f"one-{suffix}")
    _second, _ = _create_quota_test_student(client, admin_headers, parent["id"], f"two-{suffix}")

    listing = client.get("/api/v1/tutoring/admin/quotas")
    assert listing.status_code == 200
    children = [item for item in listing.json()["quotas"] if item["studentName"].startswith("Quota Student")]
    assert len(children) == 2 and children[0]["studentRef"].startswith("quota_")
    assert all(first["id"] not in item["studentRef"] for item in children)
    target = next(item for item in children if "one-" in item["studentName"])
    other = next(item for item in children if item["studentRef"] != target["studentRef"])
    updated = client.post(f"/api/v1/tutoring/admin/quotas/{target['studentRef']}", headers=admin_headers, json={
        "periodDays": 7, "requestAllowance": 3, "textTokenAllowance": 5000,
        "voiceMinuteAllowance": 12, "enabled": False, "reason": "Temporary study break",
    })
    assert updated.status_code == 200
    assert updated.json()["state"] == "disabled" and updated.json()["voiceMinutes"]["allowance"] == 12
    refreshed = client.get("/api/v1/tutoring/admin/quotas").json()["quotas"]
    untouched = next(item for item in refreshed if item["studentRef"] == other["studentRef"])
    assert untouched["enabled"] is True and untouched["requests"]["allowance"] == 100
    history = client.get(f"/api/v1/tutoring/admin/quotas/{target['studentRef']}/audit").json()
    change = next(event for event in history["events"] if event["action"] == "student_ai_quota.disabled")
    assert change["reason"] == "Temporary study break"
    increased = client.post(f"/api/v1/tutoring/admin/quotas/{target['studentRef']}", headers=admin_headers, json={
        "periodDays": 7, "requestAllowance": 4, "textTokenAllowance": 6000,
        "voiceMinuteAllowance": 15, "enabled": True, "reason": "Resume with a larger allowance",
    })
    assert increased.status_code == 200 and increased.json()["enabled"] is True
    reduced = client.post(f"/api/v1/tutoring/admin/quotas/{target['studentRef']}", headers=admin_headers, json={
        "periodDays": 7, "requestAllowance": 2, "textTokenAllowance": 4000,
        "voiceMinuteAllowance": 10, "enabled": True, "reason": "Reduce after review",
    })
    assert reduced.status_code == 200
    actions = {event["action"] for event in client.get(
        f"/api/v1/tutoring/admin/quotas/{target['studentRef']}/audit").json()["events"]}
    assert {"student_ai_quota.created", "student_ai_quota.enabled", "student_ai_quota.reduced"} <= actions

    client.post("/api/v1/auth/logout", headers=admin_headers)
    student_login = client.post("/api/v1/auth/login", json={"username": first["username"], "password": first_password}).json()
    student_headers = {"X-CSRF-Token": student_login["csrfToken"]}
    changed = client.post("/api/v1/auth/change-password", headers=student_headers,
                          json={"newPassword": "student selected quota password"})
    assert changed.status_code == 204
    status = client.get("/api/v1/tutoring/quota")
    assert status.status_code == 200 and status.json()["fallbackMessage"]
    assert client.get("/api/v1/tutoring/admin/quotas").status_code == 403
