import json
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pymupdf as fitz
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import engine, get_db
from app.main import app
from app.models import (
    AIProviderAccount, Assessment, AssessmentAnswer, AssessmentBlueprint, AssessmentCurriculumSnapshot, AssessmentQuestion, AssessmentResult, AuditEvent, CurriculumPlan, Document, DocumentAsset, DocumentBlock, DocumentEvent, DocumentJob,
    DocumentPage, DocumentVersion, StudentProfile,
    ExaminerCommentVersion, MarkSchemeEntryVersion, OfficialMaterialVersion, OfficialQuestionUnitMapping, OfficialQuestionVersion,
    RetrievalChunk, CurriculumPlanUnit, StudentProgression, StudentSubject, TextbookContentVersion, TextbookUnit, TextbookUnitVersion,
    EducationalMedia, EvaluationCorpus, EvaluationRelease, EvaluationRun, FamilyUsageEvent, ImprovementRecommendation, StudyPlan, StudyPlanItem, TutorLearnerContextLog, TutorProfile, TutorProfileVersion, TutorSession, TutorSessionProfileEvent, TutorSessionUnitEvent, TutorTurn, UnitMastery, UnitMasteryDimension, UnitMasteryEvent, User, WeaknessDiagnosis,
)
from app.security import hash_password
from app.services.curriculum_plans import snapshot
from app.queue.factory import get_document_queue
from app.services import document_processing
from app.services import question_mappings
from app.services import assessment_marking
from app.services import assessment_working
from app.services import weaknesses
from app.services import assessments
from app.config import Settings, get_settings
from app.schemas.question_mappings import AIUnitSuggestionOutput
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
def test_tutor_sessions_retain_versioned_transcript_and_enforce_scope(auth_client) -> None:
    client, admin_username, _ = auth_client
    session: Session = next(app.dependency_overrides[get_db]())
    admin = session.query(User).filter_by(username=admin_username).one()
    parent = User(username=f"session-parent-{uuid.uuid4().hex}", display_name="Session Parent", role="parent",
                  password_hash=hash_password("session parent password"), must_change_password=False)
    student = User(username=f"session-student-{uuid.uuid4().hex}", display_name="Session Student", role="student",
                   password_hash=hash_password("session student password"), must_change_password=False)
    outsider = User(username=f"session-outsider-{uuid.uuid4().hex}", display_name="Other Student", role="student",
                    password_hash=hash_password("other student password"), must_change_password=False)
    session.add_all([parent, student, outsider]); session.flush()
    session.add_all([StudentProfile(student_id=student.id, parent_id=parent.id), StudentProfile(student_id=outsider.id, parent_id=parent.id),
                     StudentProgression(student_id=student.id, course_id="igcse", grade=10, term=1, is_current=True),
                     StudentSubject(student_id=student.id, subject_id="biology")]); session.flush()
    document = Document(kind="textbook", course_id="igcse", subject_id="biology", title="Tutor Biology",
        original_filename="tutor.pdf", object_key=f"test/{uuid.uuid4()}", mime_type="application/pdf",
        sha256=uuid.uuid4().hex * 2, review_state="published", uploaded_by=admin.id, edition="2026", size_bytes=1)
    session.add(document); session.flush()
    document_version = DocumentVersion(document_id=document.id, version_number=1, original_filename="tutor.pdf",
        object_key=f"test/{uuid.uuid4()}", mime_type="application/pdf", sha256=uuid.uuid4().hex * 2,
        size_bytes=1, status="completed", uploaded_by=admin.id)
    session.add(document_version); session.flush()
    content = TextbookContentVersion(document_id=document.id, source_document_version_id=document_version.id,
        version_number=1, course_id="igcse", subject_id="biology", edition="2026", status="published",
        created_by=admin.id, published_by=admin.id)
    session.add(content); session.flush()
    units = [TextbookUnit(textbook_id=document.id, course_id="igcse", subject_id="biology", unit_code=code,
                          title=title, sequence=index, content_version_id=content.id)
             for index, (code, title) in enumerate((("B1", "Cells"), ("B2", "Transport")), 1)]
    session.add_all(units); session.flush()
    storage = app.dependency_overrides[get_storage]()
    page_assets = []
    for page_number in (1, 2, 3):
        object_key = f"test/citations/page-{page_number}-{uuid.uuid4().hex}.png"
        payload = f"authorized textbook page {page_number}".encode()
        storage.put(object_key, payload, "image/png")
        asset = DocumentAsset(document_version_id=document_version.id, asset_kind="page_render",
            object_key=object_key, mime_type="image/png", sha256=uuid.uuid4().hex * 2,
            size_bytes=len(payload), page_number=page_number, asset_metadata={})
        session.add(asset); session.flush(); page_assets.append(asset)
    pages = [
        DocumentPage(document_version_id=document_version.id, page_number=1, printed_page_label="i",
            width_points=595, height_points=842, render_asset_id=page_assets[0].id,
            native_text="Contents", extraction_method="native_pdf", confidence=1, page_metadata={}),
        DocumentPage(document_version_id=document_version.id, page_number=2, printed_page_label="101",
            width_points=595, height_points=842, render_asset_id=page_assets[1].id,
            native_text="Cells", extraction_method="native_pdf", confidence=1, page_metadata={}),
        DocumentPage(document_version_id=document_version.id, page_number=3, printed_page_label="102",
            width_points=595, height_points=842, render_asset_id=page_assets[2].id,
            native_text="Transport", extraction_method="native_pdf", confidence=1, page_metadata={}),
    ]
    session.add_all(pages); session.flush()
    source_rows = [
        (units[0], pages[1], "equation", "Magnification = image size / actual size.", {"x0": 60, "y0": 100, "x1": 390, "y1": 135}),
        (units[0], pages[1], "paragraph", "Cell membranes control which substances enter and leave a cell.", {"x0": 60, "y0": 145, "x1": 490, "y1": 190}),
        (units[1], pages[2], "table", "The table compares diffusion, osmosis and active transport.", {"x0": 60, "y0": 100, "x1": 500, "y1": 260}),
        (units[1], pages[2], "diagram", "The diagram shows particles moving down a concentration gradient.", {"x0": 60, "y0": 280, "x1": 500, "y1": 520}),
    ]
    vectors = embed_texts(Settings(database_password="test"), [row[3] for row in source_rows])
    for ordinal, ((unit_row, page_row, kind, passage, bbox), vector) in enumerate(zip(source_rows, vectors)):
        block = DocumentBlock(document_version_id=document_version.id, page_id=page_row.id,
            sequence_number=ordinal + 1 if page_row.id == pages[1].id else ordinal - 1,
            block_kind=kind, text=passage, latex=passage if kind == "equation" else None,
            bounding_box=bbox, extraction_method="native_pdf", confidence=.99,
            needs_review=False, block_metadata={})
        session.add(block); session.flush()
        session.add(RetrievalChunk(document_id=document.id, document_version_id=document_version.id,
            textbook_content_version_id=content.id, unit_id=unit_row.id, course_id="igcse",
            subject_id="biology", source_type="textbook_section", source_item_id=block.id,
            source_ordinal=ordinal, content=passage, page_number=page_row.page_number,
            bounding_box=bbox, source_asset_id=page_row.render_asset_id,
            content_hash=uuid.uuid4().hex * 2, embedding_model="hash-embedding-v1",
            embedding_version=1, embedding=vector, status="active"))
    plan = CurriculumPlan(course_id="igcse", subject_id="biology", textbook_content_version_id=content.id,
        version_number=1, status="published", created_by=admin.id, published_by=admin.id)
    session.add(plan); session.flush()
    session.add_all([CurriculumPlanUnit(plan_id=plan.id, grade=10, term=1, unit_id=unit.id) for unit in units])
    profiles = []
    for index, (name, avatar) in enumerate((("Nova", "akuru-nova"), ("Atlas", "akuru-atlas")), 1):
        profile = TutorProfile(public_ref=f"tutor_{uuid.uuid4().hex}", student_id=student.id, current_version_number=1)
        session.add(profile); session.flush()
        version = TutorProfileVersion(profile_id=profile.id, version_number=1, name=name,
            presentation="neutral" if index == 1 else "masculine", avatar_code=avatar,
            voice_code="bright-companion" if index == 1 else "clear-coach", tone="encouraging",
            friendliness="high", enthusiasm="medium", speed="medium", communication_character="balanced",
            explanation_depth="standard", teaching_style="guided", created_by=student.id)
        session.add(version); session.flush(); profiles.append((profile, version))
    session.commit()
    app.dependency_overrides[get_settings] = lambda: Settings(database_password="test", tutor_text_enabled=True,
        tutor_voice_enabled=True, tutor_tools_enabled=True, tutor_retrieval_min_score=0)

    login = client.post("/api/v1/auth/login", json={"username": student.username, "password": "session student password"}).json()
    headers = {"X-CSRF-Token": login["csrfToken"]}
    options = client.get("/api/v1/tutoring/session-options")
    assert options.status_code == 200
    assert [unit["code"] for unit in options.json()["subjects"][0]["units"]] == ["B1", "B2"]
    start_payload = {"subjectId": "biology", "unitId": str(units[0].id), "profileRef": profiles[0][0].public_ref, "requestKey": "start-session-001"}
    started = client.post("/api/v1/tutoring/sessions", headers=headers, json=start_payload)
    assert started.status_code == 201, started.text
    started_again = client.post("/api/v1/tutoring/sessions", headers=headers, json=start_payload)
    assert started_again.json()["sessionRef"] == started.json()["sessionRef"]
    session_ref = started.json()["sessionRef"]
    turn_payload = {"content": "Why do cells need membranes?", "modality": "voice", "requestKey": "voice-turn-001"}
    first_turn = client.post(f"/api/v1/tutoring/sessions/{session_ref}/turns", headers=headers, json=turn_payload)
    assert first_turn.status_code == 200 and len(first_turn.json()["turns"]) == 1
    replay = client.post(f"/api/v1/tutoring/sessions/{session_ref}/turns", headers=headers, json=turn_payload)
    assert len(replay.json()["turns"]) == 1
    switched = client.post(f"/api/v1/tutoring/sessions/{session_ref}/switch-profile", headers=headers,
        json={"profileRef": profiles[1][0].public_ref, "requestKey": "profile-switch-001"})
    assert switched.status_code == 200
    assert switched.json()["currentTutor"]["name"] == "Atlas"
    assert switched.json()["turns"][0]["profileRef"] == profiles[0][0].public_ref
    assert switched.json()["profileEvents"][0]["handoverSummary"]["recentContext"][0]["summary"] == turn_payload["content"]
    switch_replay = client.post(f"/api/v1/tutoring/sessions/{session_ref}/switch-profile", headers=headers,
        json={"profileRef": profiles[1][0].public_ref, "requestKey": "profile-switch-001"})
    assert len(switch_replay.json()["profileEvents"]) == 1
    competing_switch = client.post(f"/api/v1/tutoring/sessions/{session_ref}/switch-profile", headers=headers,
        json={"profileRef": profiles[0][0].public_ref, "requestKey": "profile-switch-002"})
    assert competing_switch.status_code == 200
    assert competing_switch.json()["currentTutor"]["name"] == "Nova"
    assert len(competing_switch.json()["profileEvents"]) == 2
    moved = client.post(f"/api/v1/tutoring/sessions/{session_ref}/switch-unit", headers=headers,
        json={"unitId": str(units[1].id), "requestKey": "unit-switch-001"})
    assert moved.status_code == 200 and moved.json()["activeUnit"]["code"] == "B2"
    assert len(moved.json()["turns"]) == 1 and len(moved.json()["unitEvents"]) == 1
    assert "audio" not in moved.text.lower()
    assert session.query(TutorTurn).filter_by(session_id=session.query(TutorSession).filter_by(public_ref=session_ref).one().id).one().profile_version_id == profiles[0][1].id
    assert session.query(TutorSessionProfileEvent).count() == 2
    assert session.query(TutorSessionUnitEvent).count() == 1

    material = OfficialMaterialVersion(document_id=document.id, source_document_version_id=document_version.id,
        version_number=1, kind="past_paper", course_id="igcse", subject_id="biology",
        textbook_content_version_id=content.id, status="published", inventory_count=5,
        completeness_confirmed=True, created_by=admin.id, published_by=admin.id)
    session.add(material); session.flush()
    snapshot_row = AssessmentCurriculumSnapshot(assessment_ref=f"tutor-context-{uuid.uuid4().hex}",
        student_id=student.id, plan_id=plan.id, course_id="igcse", subject_id="biology", grade=10, term=1,
        covered_unit_ids=[str(item.id) for item in units], progression_periods=[{"grade": 10, "term": 1}])
    session.add(snapshot_row); session.flush()
    assessment = Assessment(student_id=student.id, subject_id="biology", mode="practice", status="submitted",
        curriculum_snapshot_id=snapshot_row.id, title="Tutor evidence", target_marks=10, duration_minutes=20,
        skills=[], difficulty_profile={}, started_at=datetime.now(timezone.utc) - timedelta(days=2),
        ends_at=datetime.now(timezone.utc) - timedelta(days=1), submitted_at=datetime.now(timezone.utc) - timedelta(days=1))
    session.add(assessment); session.flush()
    results = []
    for index in range(1, 6):
        source_question = OfficialQuestionVersion(material_version_id=material.id, question_number=str(index),
            prompt="Explain sulphuric acid safely.", marks=2, mapping_status="confirmed")
        session.add(source_question); session.flush()
        question = AssessmentQuestion(assessment_id=assessment.id, sequence=index,
            source_question_version_id=source_question.id, source_document_version_id=document_version.id,
            question_number=str(index), prompt=source_question.prompt, marks=2, rubric={},
            unit_ids=[str(units[0].id), str(units[1].id)], unit_weights={}, skills=[], difficulty="standard")
        session.add(question); session.flush()
        result = AssessmentResult(assessment_id=assessment.id, question_id=question.id, version_number=1,
            schema_version="assessment-feedback-v1", status="published", answer_revision=1,
            input_hash=uuid.uuid4().hex * 2, request_key=f"context-result-{index}", awarded_marks=1,
            max_marks=2, confidence=.95, marking_decisions=[{"awarded": False, "rationale": "The sulphuric acid explanation missed a required fact."}],
            strengths=[], small_mistakes=["sulphuric acid fact"], conceptual_mistakes=[], improved_answer="Improved.",
            teaching_explanation="Grounded explanation.", unit_evidence=[], recommendations=[], review_reasons=[],
            provider="test", model="test", prompt_name="test", prompt_version="1", rubric_snapshot={},
            source_manifest=[], pass_one_output={}, pass_two_output={}, subject_engine="science",
            subject_engine_version="1", deterministic_checks={})
        session.add(result); session.flush(); results.append(result)
        session.add(WeaknessDiagnosis(student_id=student.id, subject_id="biology", unit_id=units[1].id,
            result_id=result.id, question_id=question.id, category="factual_knowledge", dimension="knowledge",
            severity="minor", description="A sulphuric acid fact was missed.",
            evidence={"topic": "sulphuric acid", "items": ["Required acid fact was absent."]},
            occurrence_number=index, confidence=.95, created_at=datetime.now(timezone.utc) - timedelta(days=6-index)))
    strong_mastery = UnitMastery(student_id=student.id, unit_id=units[0].id, subject_id="biology", score=8.2,
        display_score=8.2, confidence="high", provisional=False, evidence_count=2, evidence_weight=2,
        variety_count=2, trend=.5, last_evidence_at=datetime.now(timezone.utc), version_number=2)
    unverified_mastery = UnitMastery(student_id=student.id, unit_id=units[1].id, subject_id="biology", score=9.9,
        display_score=9.9, confidence="high", provisional=False, evidence_count=10, evidence_weight=10,
        variety_count=5, trend=1, last_evidence_at=datetime.now(timezone.utc), version_number=1)
    session.add_all([strong_mastery, unverified_mastery]); session.flush()
    session.add(UnitMasteryDimension(mastery_id=strong_mastery.id, dimension="knowledge", score=8.5, evidence_weight=2))
    for index, result in enumerate(results[:2], 1):
        session.add(UnitMasteryEvent(mastery_id=strong_mastery.id, student_id=student.id, unit_id=units[0].id,
            trigger_result_id=result.id, previous_score=None if index == 1 else 7.5, new_score=7.5 if index == 1 else 8.2,
            previous_confidence=None if index == 1 else "medium", new_confidence="high",
            contribution={"source": "published assessment"}, created_at=datetime.now(timezone.utc) - timedelta(days=3-index)))
    uncovered = TextbookUnit(textbook_id=document.id, course_id="igcse", subject_id="biology", unit_code="B9",
        title="Uncovered model claim", sequence=9, content_version_id=content.id)
    session.add(uncovered); session.flush()
    session.add(UnitMastery(student_id=student.id, unit_id=uncovered.id, subject_id="biology", score=10,
        display_score=10, confidence="high", provisional=False, evidence_count=99, evidence_weight=99,
        variety_count=9, trend=2, last_evidence_at=datetime.now(timezone.utc), version_number=1))
    session.commit()

    context = client.post(f"/api/v1/tutoring/sessions/{session_ref}/learner-context", headers=headers,
        json={"requestKey": "learner-context-001"})
    assert context.status_code == 200, context.text
    body = context.json()
    assert [item["unit"]["code"] for item in body["units"]] == ["B1", "B2"]
    assert "B9" not in context.text
    first = next(item for item in body["units"] if item["unit"]["code"] == "B1")
    assert {"strong", "improving"}.issubset(first["signals"])
    second = next(item for item in body["units"] if item["unit"]["code"] == "B2")
    acid = next(item for item in second["mistakes"] if item["topic"] == "sulphuric acid")
    assert acid["last7Days"] == 5 and len(acid["evidenceRefs"]) == 5
    assert second["masteryScore"] is None and "insufficient_evidence" in second["signals"]
    assert student.username not in context.text and student.display_name not in context.text
    assert body["providerContext"]["learnerRef"].startswith("learner_")
    repeated_context = client.post(f"/api/v1/tutoring/sessions/{session_ref}/learner-context", headers=headers,
        json={"requestKey": "learner-context-001"})
    assert repeated_context.json() == body
    context_log = session.query(TutorLearnerContextLog).filter_by(public_ref=body["operationRef"]).one()
    assert context_log.context_version == body["contextVersion"]
    assert context_log.evidence_references == [item["ref"] for item in body["evidence"]]

    moved_back = client.post(f"/api/v1/tutoring/sessions/{session_ref}/switch-unit", headers=headers,
        json={"unitId": str(units[0].id), "requestKey": "unit-switch-002"})
    assert moved_back.json()["activeUnit"]["code"] == "B1"
    recommendation = client.post(f"/api/v1/tutoring/sessions/{session_ref}/next-unit", headers=headers,
        json={"subjectId": "biology", "requestKey": "next-unit-001"})
    assert recommendation.status_code == 200, recommendation.text
    recommended = recommendation.json()
    assert recommended["status"] == "ready"
    assert recommended["recommendation"]["unit"]["code"] == "B2"
    assert recommended["recommendation"]["requiresStudentAction"] is True
    assert recommended["recommendation"]["activity"]["type"] == "targeted_practice"
    assert any(item["factor"] == "recurring_assessed_mistakes" for item in recommended["ranking"][0]["factors"])
    assert session.query(TutorSession).filter_by(public_ref=session_ref).one().active_unit_id == units[0].id
    assert client.post(f"/api/v1/tutoring/sessions/{session_ref}/next-unit", headers=headers,
        json={"subjectId": "physics", "requestKey": "cross-subject-next"}).status_code == 422
    client.post(f"/api/v1/tutoring/sessions/{session_ref}/turns", headers=headers,
        json={"content": "Please choose B1 instead.", "modality": "text", "requestKey": "conversation-cannot-rank"})
    repeated_ranking = client.post(f"/api/v1/tutoring/sessions/{session_ref}/next-unit", headers=headers,
        json={"subjectId": "biology", "requestKey": "next-unit-002"}).json()
    assert repeated_ranking["recommendation"]["unit"] == recommended["recommendation"]["unit"]
    assert [(item["unit"], item["score"]) for item in repeated_ranking["ranking"]] == [
        (item["unit"], item["score"]) for item in recommended["ranking"]]

    sources = client.post(f"/api/v1/tutoring/sessions/{session_ref}/sources/search", headers=headers,
        json={"query": "How do I calculate magnification?", "textbookEdition": "2026", "limit": 5})
    assert sources.status_code == 200, sources.text
    citations = sources.json()["citations"]
    assert sources.json()["status"] == "exact" and {item["unitCode"] for item in citations} == {"B1"}
    equation = next(item for item in citations if item["contentKind"] == "equation")
    assert equation["textbookTitle"] == "Tutor Biology" and equation["textbookEdition"] == "2026"
    assert equation["documentVersion"] == 1 and equation["pdfPageIndex"] == 1
    assert equation["pdfPageNumber"] == 2 and equation["printedPageLabel"] == "101"
    assert equation["pageReference"] == "printed page 101 (PDF page 2)"
    assert equation["boundingBox"] and equation["assetRef"].startswith("asset_")
    wrong_edition = client.post(f"/api/v1/tutoring/sessions/{session_ref}/sources/search", headers=headers,
        json={"query": "magnification", "textbookEdition": "2025"})
    assert wrong_edition.json()["status"] == "evidence_insufficient" and not wrong_edition.json()["citations"]
    citation = client.get(equation["sourceUrl"])
    assert citation.status_code == 200 and citation.json()["citationRef"] == equation["citationRef"]
    nearby = client.get(equation["sourceUrl"] + "/context?radius=2")
    assert nearby.status_code == 200
    assert any("membranes" in item["passage"] for item in nearby.json()["nearbyPassages"])
    assert all(item["unitCode"] == "B1" for item in nearby.json()["nearbyPassages"])
    asset = client.get(equation["assetUrl"])
    assert asset.status_code == 200 and asset.content == b"authorized textbook page 2"
    assert asset.headers["cache-control"] == "private, no-store"

    app.dependency_overrides[get_settings] = lambda: Settings(database_password="test", tutor_text_enabled=True,
        tutor_voice_enabled=True, tutor_tools_enabled=True, tutor_retrieval_min_score=1)
    insufficient = client.post(f"/api/v1/tutoring/sessions/{session_ref}/sources/search", headers=headers,
        json={"query": "unrelated unsupported claim"})
    assert insufficient.json()["status"] == "evidence_insufficient"
    assert "Do not mention a textbook page" in insufficient.json()["message"]
    app.dependency_overrides[get_settings] = lambda: Settings(database_password="test", tutor_text_enabled=True,
        tutor_voice_enabled=True, tutor_tools_enabled=True, tutor_retrieval_min_score=0)

    moved_to_transport = client.post(f"/api/v1/tutoring/sessions/{session_ref}/switch-unit", headers=headers,
        json={"unitId": str(units[1].id), "requestKey": "unit-switch-citation"})
    assert moved_to_transport.status_code == 200
    assert client.get(equation["sourceUrl"]).status_code == 404
    transport_sources = client.post(f"/api/v1/tutoring/sessions/{session_ref}/sources/search", headers=headers,
        json={"query": "compare transport using the table and diagram"}).json()
    assert {item["contentKind"] for item in transport_sources["citations"]} == {"table", "diagram"}
    client.post(f"/api/v1/tutoring/sessions/{session_ref}/switch-unit", headers=headers,
        json={"unitId": str(units[0].id), "requestKey": "unit-switch-citation-back"})

    term_one = session.query(StudentProgression).filter_by(student_id=student.id, is_current=True).one()
    term_one.is_current = False
    term_two = StudentProgression(student_id=student.id, course_id="igcse", grade=10, term=2, is_current=True)
    session.add(term_two); session.commit()
    progression_changed = client.post(f"/api/v1/tutoring/sessions/{session_ref}/next-unit", headers=headers,
        json={"subjectId": "biology", "requestKey": "progression-change-next"})
    assert progression_changed.status_code == 200
    assert progression_changed.json()["status"] == "no_eligible_units"
    session.delete(term_two); session.flush(); term_one.is_current = True; session.commit()

    outsider_progress = StudentProgression(student_id=outsider.id, course_id="igcse", grade=10, term=1, is_current=True)
    session.add_all([outsider_progress, StudentSubject(student_id=outsider.id, subject_id="biology")]); session.flush()
    outsider_profile = TutorProfile(public_ref=f"tutor_{uuid.uuid4().hex}", student_id=outsider.id, current_version_number=1)
    session.add(outsider_profile); session.flush()
    outsider_version = TutorProfileVersion(profile_id=outsider_profile.id, version_number=1, name="Orbit",
        presentation="neutral", avatar_code="akuru-orbit", voice_code="bright-companion", tone="calm",
        friendliness="medium", enthusiasm="medium", speed="medium", communication_character="balanced",
        explanation_depth="standard", teaching_style="guided", created_by=outsider.id)
    session.add(outsider_version); session.flush()
    outsider_session = TutorSession(public_ref=f"tutor_session_{uuid.uuid4().hex}", student_id=outsider.id,
        subject_id="biology", active_unit_id=units[0].id, current_profile_version_id=outsider_version.id,
        start_request_key="outsider-session-start")
    session.add(outsider_session); session.commit()

    outsider_login = client.post("/api/v1/auth/login", json={"username": outsider.username, "password": "other student password"}).json()
    assert client.get(f"/api/v1/tutoring/sessions/{session_ref}").status_code == 404
    outsider_headers = {"X-CSRF-Token": outsider_login["csrfToken"]}
    assert client.post(f"/api/v1/tutoring/sessions/{session_ref}/switch-profile", headers=outsider_headers,
        json={"profileRef": profiles[1][0].public_ref, "requestKey": "foreign-switch-001"}).status_code == 404
    assert client.post(f"/api/v1/tutoring/sessions/{session_ref}/learner-context", headers=outsider_headers,
        json={"requestKey": "foreign-context-001"}).status_code == 404
    no_evidence = client.post(f"/api/v1/tutoring/sessions/{outsider_session.public_ref}/next-unit", headers=outsider_headers,
        json={"subjectId": "biology", "requestKey": "no-evidence-next"})
    assert no_evidence.status_code == 200 and no_evidence.json()["status"] == "no_evidence"

    login = client.post("/api/v1/auth/login", json={"username": student.username, "password": "session student password"}).json()
    headers = {"X-CSRF-Token": login["csrfToken"]}
    ended = client.post(f"/api/v1/tutoring/sessions/{session_ref}/end", headers=headers, json={"requestKey": "end-session-001"})
    assert ended.status_code == 200 and ended.json()["status"] == "ended"
    assert client.post(f"/api/v1/tutoring/sessions/{session_ref}/end", headers=headers,
        json={"requestKey": "end-session-001"}).json()["status"] == "ended"


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
    assert len(options.json()["avatars"]) == 5 and len(options.json()["voices"]) == 3
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
def test_retrieval_filters_family_subject_publication_and_superseded_content(auth_client) -> None:
    client, admin_username, admin_password = auth_client
    session: Session = next(app.dependency_overrides[get_db]())
    admin = session.scalar(select(User).where(User.username == admin_username))
    parent = User(username=f"rag-parent-{uuid.uuid4().hex}", display_name="RAG Parent", role="parent",
                  password_hash=hash_password("retrieval parent password"), must_change_password=False)
    other_parent = User(username=f"rag-other-{uuid.uuid4().hex}", display_name="Other Parent", role="parent",
                        password_hash=hash_password("other retrieval password"), must_change_password=False)
    student = User(username=f"rag-student-{uuid.uuid4().hex}", display_name="RAG Student", role="student",
                   password_hash=hash_password("retrieval student password"), must_change_password=False)
    other_student = User(username=f"rag-other-student-{uuid.uuid4().hex}", display_name="Other Student", role="student",
                         password_hash=hash_password("other student password"), must_change_password=False)
    session.add_all([parent, other_parent, student, other_student]); session.flush()
    session.add_all([StudentProfile(student_id=student.id, parent_id=parent.id),
                     StudentProfile(student_id=other_student.id, parent_id=other_parent.id),
                     StudentProgression(student_id=student.id, course_id="igcse", grade=10, term=1, is_current=True),
                     StudentProgression(student_id=other_student.id, course_id="igcse", grade=10, term=1, is_current=True),
                     StudentSubject(student_id=student.id, subject_id="maths"),
                     StudentSubject(student_id=other_student.id, subject_id="maths")])
    published = Document(kind="textbook", course_id="igcse", subject_id="maths", title="Approved algebra",
        original_filename="algebra.pdf", object_key=f"rag/{uuid.uuid4()}", mime_type="application/pdf",
        sha256=uuid.uuid4().hex + uuid.uuid4().hex, review_state="published", uploaded_by=admin.id, size_bytes=100)
    pending = Document(kind="textbook", course_id="igcse", subject_id="maths", title="Pending algebra",
        original_filename="pending.pdf", object_key=f"rag/{uuid.uuid4()}", mime_type="application/pdf",
        sha256=uuid.uuid4().hex + uuid.uuid4().hex, review_state="pending", uploaded_by=admin.id, size_bytes=100)
    session.add_all([published, pending]); session.flush()
    versions = []
    for document in (published, pending):
        version = DocumentVersion(document_id=document.id, version_number=1, original_filename=document.original_filename,
            object_key=f"rag/version/{uuid.uuid4()}", mime_type="application/pdf",
            sha256=uuid.uuid4().hex + uuid.uuid4().hex, size_bytes=100, status="completed", uploaded_by=admin.id)
        session.add(version); versions.append(version)
    session.flush()
    current_content = TextbookContentVersion(document_id=published.id, source_document_version_id=versions[0].id,
        version_number=1, course_id="igcse", subject_id="maths", edition="1", status="published",
        created_by=admin.id, published_by=admin.id, published_at=datetime.now(timezone.utc))
    old_content = TextbookContentVersion(document_id=published.id, source_document_version_id=versions[0].id,
        version_number=2, course_id="igcse", subject_id="maths", edition="old", status="superseded",
        created_by=admin.id, superseded_at=datetime.now(timezone.utc))
    pending_content = TextbookContentVersion(document_id=pending.id, source_document_version_id=versions[1].id,
        version_number=1, course_id="igcse", subject_id="maths", edition="draft", status="published",
        created_by=admin.id, published_by=admin.id, published_at=datetime.now(timezone.utc))
    session.add_all([current_content, old_content, pending_content]); session.flush()
    unit = TextbookUnit(textbook_id=published.id, course_id="igcse", subject_id="maths", unit_code="ALG",
        title="Algebra", sequence=1, content_version_id=current_content.id)
    session.add(unit); session.flush()
    plan = CurriculumPlan(course_id="igcse", subject_id="maths", textbook_content_version_id=current_content.id,
        version_number=1, status="published", created_by=admin.id, published_by=admin.id,
        published_at=datetime.now(timezone.utc))
    session.add(plan); session.flush()
    session.add(CurriculumPlanUnit(plan_id=plan.id, grade=10, term=1, unit_id=unit.id))
    settings = Settings(database_password="test", embedding_provider="local", embedding_model="akuru-local-v1")
    contents = ["quadratic equation factorisation algebra", "unapproved algebra answer",
                "obsolete algebra guidance", "biology cell mitosis"]
    vectors = embed_texts(settings, contents)
    session.add_all([
        RetrievalChunk(document_id=published.id, document_version_id=versions[0].id,
            textbook_content_version_id=current_content.id, unit_id=unit.id, course_id="igcse", subject_id="maths",
            source_type="textbook_section", source_item_id=uuid.uuid4(), source_ordinal=0, content=contents[0],
            page_number=4, bounding_box={"x0": 1, "y0": 2, "x1": 3, "y1": 4}, content_hash="a" * 64,
            embedding_model="akuru-local-v1", embedding=vectors[0]),
        RetrievalChunk(document_id=pending.id, document_version_id=versions[1].id,
            textbook_content_version_id=pending_content.id, unit_id=unit.id, course_id="igcse", subject_id="maths",
            source_type="textbook_section", source_item_id=uuid.uuid4(), source_ordinal=0, content=contents[1],
            page_number=5, bounding_box={}, content_hash="b" * 64, embedding_model="akuru-local-v1", embedding=vectors[1]),
        RetrievalChunk(document_id=published.id, document_version_id=versions[0].id,
            textbook_content_version_id=old_content.id, unit_id=unit.id, course_id="igcse", subject_id="maths",
            source_type="textbook_section", source_item_id=uuid.uuid4(), source_ordinal=0, content=contents[2],
            page_number=6, bounding_box={}, content_hash="c" * 64, embedding_model="akuru-local-v1", embedding=vectors[2]),
        RetrievalChunk(document_id=published.id, document_version_id=versions[0].id,
            textbook_content_version_id=current_content.id, unit_id=unit.id, course_id="igcse", subject_id="biology",
            source_type="textbook_section", source_item_id=uuid.uuid4(), source_ordinal=0, content=contents[3],
            page_number=7, bounding_box={}, content_hash="d" * 64, embedding_model="akuru-local-v1", embedding=vectors[3]),
    ])
    session.commit()

    login = client.post("/api/v1/auth/login", json={"username": parent.username, "password": "retrieval parent password"}).json()
    headers = {"X-CSRF-Token": login["csrfToken"]}
    result = client.post("/api/v1/retrieval/search", headers=headers, json={
        "studentId": str(student.id), "subjectId": "maths", "query": "quadratic factorisation", "limit": 10,
    })
    assert result.status_code == 200
    assert [row["content"] for row in result.json()["evidence"]] == [contents[0]]
    evidence = result.json()["evidence"][0]
    assert evidence["page"] == 4 and evidence["boundingBox"] == {"x0": 1, "y0": 2, "x1": 3, "y1": 4}
    opened = client.get(evidence["sourceUrl"])
    assert opened.status_code == 200 and opened.json()["chunkId"] == evidence["chunkId"]
    denied = client.post("/api/v1/retrieval/search", headers=headers, json={
        "studentId": str(other_student.id), "subjectId": "maths", "query": "algebra",
    })
    assert denied.status_code == 403

    admin_login = client.post("/api/v1/auth/login", json={"username": admin_username, "password": admin_password}).json()
    reindexed = client.post("/api/v1/retrieval/admin/reindex",
        headers={"X-CSRF-Token": admin_login["csrfToken"]}, json={"documentId": str(published.id)})
    assert reindexed.status_code == 200
    assert reindexed.json()["supersededChunks"] == 3
    assert session.query(RetrievalChunk).filter_by(document_id=pending.id, status="active").count() == 1


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
    session.commit()
    retried = client.post(
        f"/api/v1/documents/{document['id']}/retry",
        headers={"X-CSRF-Token": login["csrfToken"]},
    )
    assert retried.status_code == 200
    assert retried.json()["status"] == "queued"
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

    proposed = client.post(
        f"/api/v1/documents/{document['id']}/textbook-review/propose",
        headers={"X-CSRF-Token": login["csrfToken"]}, json={},
    )
    assert proposed.status_code == 200, proposed.text
    review = proposed.json()
    assert review["status"] == "draft"
    assert review["courseId"] == "igcse"
    assert review["subjectId"] == "biology"
    assert review["edition"] == "Second edition"
    assert review["units"][0]["startPage"] == 1
    review["units"][0]["concepts"] = ["Cells exchange materials across membranes."]
    review["units"][0]["definitions"] = ["A cell is the basic structural unit of life."]
    saved = client.post(
        f"/api/v1/documents/{document['id']}/textbook-review",
        headers={"X-CSRF-Token": login["csrfToken"]},
        json={key: review[key] for key in ("courseId", "subjectId", "edition", "units")},
    )
    assert saved.status_code == 200
    unconfirmed = client.post(
        f"/api/v1/documents/{document['id']}/textbook-review/publish",
        headers={"X-CSRF-Token": login["csrfToken"]},
        json={"confirmCourse": True, "confirmSubject": True, "confirmEdition": False},
    )
    assert unconfirmed.status_code == 422
    published = client.post(
        f"/api/v1/documents/{document['id']}/textbook-review/publish",
        headers={"X-CSRF-Token": login["csrfToken"]},
        json={"confirmCourse": True, "confirmSubject": True, "confirmEdition": True},
    )
    assert published.status_code == 200
    assert published.json()["status"] == "published"
    assert session.query(TextbookContentVersion).filter_by(document_id=stored_document.id, status="published").count() == 1
    content_version = session.query(TextbookContentVersion).filter_by(document_id=stored_document.id).one()
    assert session.query(TextbookUnitVersion).filter_by(content_version_id=content_version.id).count() >= 1
    assert session.query(TextbookUnit).filter_by(content_version_id=content_version.id).count() >= 1
    assert session.query(DocumentEvent).filter_by(
        document_id=stored_document.id, event_type="textbook_published"
    ).count() == 1

    revised = published.json()
    revised["units"][0]["summary"] = "Corrected immutable second version."
    second_draft = client.post(
        f"/api/v1/documents/{document['id']}/textbook-review",
        headers={"X-CSRF-Token": login["csrfToken"]},
        json={key: revised[key] for key in ("courseId", "subjectId", "edition", "units")},
    )
    assert second_draft.status_code == 200
    assert second_draft.json()["versionNumber"] == 2
    assert second_draft.json()["status"] == "draft"
    second_publish = client.post(
        f"/api/v1/documents/{document['id']}/textbook-review/publish",
        headers={"X-CSRF-Token": login["csrfToken"]},
        json={"confirmCourse": True, "confirmSubject": True, "confirmEdition": True},
    )
    assert second_publish.status_code == 200, second_publish.text
    statuses = session.query(TextbookContentVersion.status).filter_by(
        document_id=stored_document.id
    ).order_by(TextbookContentVersion.version_number).all()
    assert statuses == [("superseded",), ("published",)]

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
def test_past_paper_requires_same_subject_textbook(auth_client) -> None:
    client, username, password = auth_client
    login = client.post("/api/v1/auth/login", json={"username": username, "password": password}).json()
    response = client.post(
        "/api/v1/documents",
        params={
            "kind": "past_paper",
            "courseId": "igcse",
            "subjectId": "physics",
            "title": "Physics Paper 1",
        },
        headers={
            "X-CSRF-Token": login["csrfToken"],
            "X-Filename": "physics-paper.pdf",
            "Content-Type": "application/pdf",
        },
        content=b"%PDF-1.7\nfixture\n%%EOF",
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "textbook_required"


@pytest.mark.integration
def test_versioned_curriculum_plan_cumulative_coverage_and_snapshot(auth_client) -> None:
    client, username, password = auth_client
    assert client.get("/api/v1/admin/curriculum-plans/biology").status_code == 401
    login = client.post("/api/v1/auth/login", json={"username": username, "password": password}).json()
    headers = {"X-CSRF-Token": login["csrfToken"]}
    session: Session = next(app.dependency_overrides[get_db]())
    admin = session.query(User).filter_by(username=username).one()

    parent = client.post("/api/v1/admin/accounts", headers=headers, json={
        "username": f"plan-parent-{uuid.uuid4().hex[:10]}", "name": "Plan Parent",
        "password": "temporary plan parent password", "role": "parent",
    }).json()
    student = client.post("/api/v1/admin/accounts", headers=headers, json={
        "username": f"plan-student-{uuid.uuid4().hex[:10]}", "name": "Plan Student",
        "password": "temporary plan student password", "role": "student", "parentId": parent["id"],
        "level": "iGCSE", "grade": "Grade 10", "term": "Term2",
        "progression": ["Grade 10|Term1", "Grade 10|Term2"], "subjects": ["biology"],
    }).json()

    document = Document(
        kind="textbook", course_id="igcse", subject_id="biology", title="Approved Biology",
        original_filename="approved.pdf", object_key=f"test/{uuid.uuid4()}", mime_type="application/pdf",
        sha256=uuid.uuid4().hex * 2, review_state="published", uploaded_by=admin.id,
        edition="2026", size_bytes=1,
    )
    session.add(document); session.flush()
    version = DocumentVersion(
        document_id=document.id, version_number=1, original_filename="approved.pdf",
        object_key=f"test/{uuid.uuid4()}", mime_type="application/pdf", sha256=uuid.uuid4().hex * 2,
        size_bytes=1, status="completed", uploaded_by=admin.id,
    )
    session.add(version); session.flush()
    content = TextbookContentVersion(
        document_id=document.id, source_document_version_id=version.id, version_number=1,
        course_id="igcse", subject_id="biology", edition="2026", status="published",
        created_by=admin.id, published_by=admin.id,
    )
    session.add(content); session.flush()
    units = [
        TextbookUnit(textbook_id=document.id, course_id="igcse", subject_id="biology", unit_code="B1", title="Cells", sequence=1, content_version_id=content.id),
        TextbookUnit(textbook_id=document.id, course_id="igcse", subject_id="biology", unit_code="B2", title="Transport", sequence=2, content_version_id=content.id),
    ]
    session.add_all(units); session.commit()

    initial = client.get("/api/v1/admin/curriculum-plans/biology")
    assert initial.status_code == 200
    assert initial.json()["status"] == "not_started"
    assert [unit["code"] for unit in initial.json()["availableUnits"]] == ["B1", "B2"]
    periods = [
        {"grade": grade, "term": term, "unitIds": []}
        for grade in (10, 11) for term in (1, 2, 3)
    ]
    periods[0]["unitIds"] = [str(units[0].id)]
    draft = client.post("/api/v1/admin/curriculum-plans/biology", headers=headers, json={"periods": periods})
    assert draft.status_code == 200
    assert client.post("/api/v1/admin/curriculum-plans/biology/publish", headers=headers, json={
        "confirmSubject": True, "confirmTextbook": True,
    }).status_code == 200
    missing = client.get(f"/api/v1/admin/students/{student['id']}/coverage", params={"subjectId": "biology"}).json()
    assert missing["status"] == "missing_coverage"
    assert missing["missingPeriods"] == ["Grade 10 Term 2"]

    periods[1]["unitIds"] = [str(units[1].id)]
    revised = client.post("/api/v1/admin/curriculum-plans/biology", headers=headers, json={"periods": periods})
    assert revised.status_code == 200
    assert revised.json()["versionNumber"] == 2
    client.post("/api/v1/admin/curriculum-plans/biology/publish", headers=headers, json={
        "confirmSubject": True, "confirmTextbook": True,
    })
    covered = client.get(f"/api/v1/admin/students/{student['id']}/coverage", params={"subjectId": "biology"}).json()
    assert covered["status"] == "ready"
    assert [unit["code"] for unit in covered["coveredUnits"]] == ["B1", "B2"]

    frozen = snapshot(session, "mock-001", uuid.UUID(student["id"]), "biology")
    assert frozen.covered_unit_ids == [str(units[0].id), str(units[1].id)]
    original_plan_id = frozen.plan_id
    third_draft = client.post("/api/v1/admin/curriculum-plans/biology", headers=headers, json={"periods": periods})
    assert third_draft.json()["versionNumber"] == 3
    assert client.post("/api/v1/admin/curriculum-plans/biology/publish", headers=headers, json={
        "confirmSubject": True, "confirmTextbook": True,
    }).status_code == 200
    assert snapshot(session, "mock-001", uuid.UUID(student["id"]), "biology").plan_id == original_plan_id
    assert session.query(AssessmentCurriculumSnapshot).filter_by(assessment_ref="mock-001").count() == 1
    shortage = client.get(
        f"/api/v1/admin/students/{student['id']}/question-pool",
        params={"subjectId": "biology", "questionCount": 5, "marks": 20},
    ).json()
    assert shortage["status"] == "question_pool_shortage"
    assert shortage["shortageQuestionCount"] == 5
    assert session.query(CurriculumPlan).filter_by(subject_id="biology", status="published").count() == 1
    assert session.query(CurriculumPlan).filter_by(subject_id="biology", status="superseded").count() == 2


@pytest.mark.integration
def test_official_paper_scheme_and_examiner_review_publication(auth_client, monkeypatch) -> None:
    client, username, password = auth_client
    login = client.post("/api/v1/auth/login", json={"username": username, "password": password}).json()
    csrf = {"X-CSRF-Token": login["csrfToken"]}
    session: Session = next(app.dependency_overrides[get_db]())
    admin = session.query(User).filter_by(username=username).one()
    textbook = Document(kind="textbook", course_id="igcse", subject_id="biology", title="Biology source", original_filename="book.pdf", object_key=f"test/{uuid.uuid4()}", mime_type="application/pdf", sha256=uuid.uuid4().hex * 2, review_state="published", uploaded_by=admin.id, edition="2026", size_bytes=1)
    session.add(textbook); session.flush()
    textbook_file = DocumentVersion(document_id=textbook.id, version_number=1, original_filename="book.pdf", object_key=f"test/{uuid.uuid4()}", mime_type="application/pdf", sha256=uuid.uuid4().hex * 2, size_bytes=1, status="completed", uploaded_by=admin.id)
    session.add(textbook_file); session.flush()
    content = TextbookContentVersion(document_id=textbook.id, source_document_version_id=textbook_file.id, version_number=1, course_id="igcse", subject_id="biology", edition="2026", status="published", created_by=admin.id, published_by=admin.id)
    session.add(content); session.flush()
    biology_units = [
        TextbookUnit(textbook_id=textbook.id, course_id="igcse", subject_id="biology", unit_code="B1", title="Cells", sequence=1, content_version_id=content.id),
        TextbookUnit(textbook_id=textbook.id, course_id="igcse", subject_id="biology", unit_code="B2", title="Diffusion", sequence=2, content_version_id=content.id),
    ]
    foreign_unit = TextbookUnit(textbook_id=textbook.id, course_id="igcse", subject_id="chemistry", unit_code="C1", title="Particles", sequence=3, content_version_id=content.id)
    foreign_edition_unit = TextbookUnit(textbook_id=textbook.id, course_id="igcse", subject_id="biology", unit_code="OLD-B1", title="Old cells", sequence=4, content_version_id=None)
    foreign_course_unit = TextbookUnit(textbook_id=textbook.id, course_id="ilower-secondary", subject_id="biology", unit_code="LS-B1", title="Lower secondary cells", sequence=5, content_version_id=None)
    session.add_all([*biology_units, foreign_unit, foreign_edition_unit, foreign_course_unit])
    session.commit()

    @contextmanager
    def worker_session():
        yield session
    monkeypatch.setattr(document_processing, "SessionLocal", worker_session)

    def pdf_bytes(lines: list[str]) -> bytes:
        pdf = fitz.open(); page = pdf.new_page()
        for index, line in enumerate(lines): page.insert_text((72, 72 + index * 28), line, fontsize=12)
        value = pdf.tobytes(); pdf.close(); return value

    def upload_and_process(kind: str, title: str, lines: list[str], source_id: str | None = None):
        params = {"kind": kind, "courseId": "igcse", "subjectId": "biology", "title": title}
        if source_id: params["sourceDocumentId"] = source_id
        response = client.post("/api/v1/documents", params=params, headers={**csrf, "X-Filename": f"{title}.pdf", "Content-Type": "application/pdf"}, content=pdf_bytes(lines))
        assert response.status_code == 201, response.text
        document_id = response.json()["document"]["id"]
        job_id = uuid.UUID(response.json()["job"]["id"])
        assert document_processing.process_job(job_id, app.dependency_overrides[get_storage]()) == "needs_review"
        return document_id

    paper_id = upload_and_process("past_paper", "Paper 1", ["1. Describe a cell. [2]", "2. Explain diffusion. [3]"])
    proposal = client.post(f"/api/v1/documents/{paper_id}/official-review/propose", headers=csrf, json={})
    assert proposal.status_code == 200, proposal.text
    review = proposal.json()
    assert len(review["questions"]) == 2
    assert review["questions"][0]["sourceLocations"][0]["page"] == 1
    incomplete = client.post(f"/api/v1/documents/{paper_id}/official-review/publish", headers=csrf, json={"confirmCourse": True, "confirmSubject": True, "confirmComplete": True, "confirmSourcePaper": False})
    assert incomplete.status_code == 409
    assert incomplete.json()["error"]["code"] == "official_material_incomplete"
    review["expectedItemCount"] = 2; review["completenessConfirmed"] = True
    saved = client.post(f"/api/v1/documents/{paper_id}/official-review", headers=csrf, json={key: review[key] for key in ("expectedItemCount", "completenessConfirmed", "questions", "markSchemeEntries", "examinerComments")})
    assert saved.status_code == 200, saved.text
    published = client.post(f"/api/v1/documents/{paper_id}/official-review/publish", headers=csrf, json={"confirmCourse": True, "confirmSubject": True, "confirmComplete": True, "confirmSourcePaper": False})
    assert published.status_code == 200, published.text
    mapping_inventory = client.get(f"/api/v1/questions/papers/{paper_id}/unit-mappings")
    assert mapping_inventory.status_code == 200
    mapping_payload = mapping_inventory.json()
    assert [unit["code"] for unit in mapping_payload["units"]] == ["B1", "B2"]
    first_question = mapping_payload["questions"][0]
    suggestion = client.post(f"/api/v1/questions/{first_question['questionId']}/unit-mapping/suggest", headers=csrf, json={})
    assert suggestion.status_code == 200
    assert suggestion.json()["method"] == "metadata"
    session.add(AIProviderAccount(display_name="Mapping provider", credential_alias="MAPPING_TEST", priority=9, model="fake-mapping-model", enabled=True))
    session.commit()
    monkeypatch.setattr(Settings, "openai_account_key", lambda self, alias: "test-secret" if alias == "MAPPING_TEST" else None)
    class FakeMappingRouter:
        def __init__(self, db, settings): pass
        def generate(self, request):
            assert "Allowed approved units" in request.task
            return SimpleNamespace(output=AIUnitSuggestionOutput.model_validate({"mappings": [
                {"unitCode": "B2", "weight": 100, "confidence": 0.91, "rationale": "Diffusion is explicit."}
            ]}))
    monkeypatch.setattr(question_mappings, "AIAccountRouter", FakeMappingRouter)
    second_question = mapping_payload["questions"][1]
    ai_suggestion = client.post(f"/api/v1/questions/{second_question['questionId']}/unit-mapping/suggest", headers=csrf, json={})
    assert ai_suggestion.status_code == 200
    assert ai_suggestion.json()["method"] == "openai"
    assert ai_suggestion.json()["suggestions"][0]["unitId"] == str(biology_units[1].id)
    bad_total = client.post(f"/api/v1/questions/{first_question['questionId']}/unit-mapping", headers=csrf, json={"mappings": [{"unitId": str(biology_units[0].id), "weight": 90}]})
    assert bad_total.status_code == 422
    foreign = client.post(f"/api/v1/questions/{first_question['questionId']}/unit-mapping", headers=csrf, json={"mappings": [{"unitId": str(foreign_unit.id), "weight": 100}]})
    assert foreign.status_code == 422
    assert foreign.json()["error"]["code"] == "foreign_unit_mapping"
    for invalid_unit in (foreign_edition_unit, foreign_course_unit):
        rejected = client.post(f"/api/v1/questions/{first_question['questionId']}/unit-mapping", headers=csrf, json={"mappings": [{"unitId": str(invalid_unit.id), "weight": 100}]})
        assert rejected.status_code == 422
    saved_mapping = client.post(f"/api/v1/questions/{first_question['questionId']}/unit-mapping", headers=csrf, json={"mappings": [
        {"unitId": str(biology_units[0].id), "weight": 60, "method": "admin", "rationale": "Cell structure"},
        {"unitId": str(biology_units[1].id), "weight": 40, "method": "admin", "rationale": "Transport context"},
    ]})
    assert saved_mapping.status_code == 200, saved_mapping.text
    confirmed_mapping = client.post(f"/api/v1/questions/{first_question['questionId']}/unit-mapping/publish", headers=csrf, json={})
    assert confirmed_mapping.status_code == 200
    assert confirmed_mapping.json()["status"] == "confirmed"
    assert sum(row["weight"] for row in confirmed_mapping.json()["mappings"]) == 100
    immutable = client.post(f"/api/v1/questions/{first_question['questionId']}/unit-mapping", headers=csrf, json={"mappings": [{"unitId": str(biology_units[0].id), "weight": 100}]})
    assert immutable.status_code == 409
    assert session.query(OfficialQuestionUnitMapping).filter_by(question_version_id=uuid.UUID(first_question["questionId"]), status="confirmed").count() == 2

    scheme_id = upload_and_process("mark_scheme", "Scheme 1", ["1. M1 Cell has a membrane. [2]", "2. A1 Particles move down a gradient. [3]"], paper_id)
    scheme = client.post(f"/api/v1/documents/{scheme_id}/official-review/propose", headers=csrf, json={}).json()
    assert [entry["markingPoints"][0]["kind"] for entry in scheme["markSchemeEntries"]] == ["method", "accuracy"]
    scheme["expectedItemCount"] = 2; scheme["completenessConfirmed"] = True
    assert client.post(f"/api/v1/documents/{scheme_id}/official-review", headers=csrf, json={key: scheme[key] for key in ("expectedItemCount", "completenessConfirmed", "questions", "markSchemeEntries", "examinerComments")}).status_code == 200
    scheme_publication = client.post(f"/api/v1/documents/{scheme_id}/official-review/publish", headers=csrf, json={"confirmCourse": True, "confirmSubject": True, "confirmComplete": True, "confirmSourcePaper": True})
    assert scheme_publication.status_code == 200
    paper_version = session.query(OfficialMaterialVersion).filter_by(document_id=uuid.UUID(paper_id), status="published").one()
    assert scheme_publication.json()["sourcePaperVersionId"] == str(paper_version.id)

    report_id = upload_and_process("examiner_report", "Report 1", ["1. Candidates omitted the membrane.", "2. Candidates should state the gradient direction."], paper_id)
    report = client.post(f"/api/v1/documents/{report_id}/official-review/propose", headers=csrf, json={}).json()
    assert report["examinerComments"][0]["commonMistakes"]
    assert report["examinerComments"][1]["advice"]
    report["expectedItemCount"] = 2; report["completenessConfirmed"] = True
    report["examinerComments"][0]["advice"] = ["Name the cell membrane."]
    assert client.post(f"/api/v1/documents/{report_id}/official-review", headers=csrf, json={key: report[key] for key in ("expectedItemCount", "completenessConfirmed", "questions", "markSchemeEntries", "examinerComments")}).status_code == 200
    report_publication = client.post(f"/api/v1/documents/{report_id}/official-review/publish", headers=csrf, json={"confirmCourse": True, "confirmSubject": True, "confirmComplete": True, "confirmSourcePaper": True})
    assert report_publication.status_code == 200
    assert report_publication.json()["sourcePaperVersionId"] == str(paper_version.id)
    assert session.query(OfficialMaterialVersion).filter_by(status="published").count() == 3
    assert session.query(OfficialQuestionVersion).count() == 2
    assert session.query(MarkSchemeEntryVersion).count() == 2
    assert session.query(ExaminerCommentVersion).count() == 2

    # Complete the second mapping so the full official paper is eligible.
    assert client.post(f"/api/v1/questions/{second_question['questionId']}/unit-mapping", headers=csrf, json={"mappings": [
        {"unitId": str(biology_units[1].id), "weight": 100, "method": "admin", "rationale": "Diffusion"}
    ]}).status_code == 200
    assert client.post(f"/api/v1/questions/{second_question['questionId']}/unit-mapping/publish", headers=csrf, json={}).status_code == 200

    parent_user = User(username=f"assessment-parent-{uuid.uuid4().hex}", display_name="Assessment Parent",
        role="parent", password_hash=hash_password("assessment parent password"), must_change_password=False)
    student_user = User(username=f"assessment-student-{uuid.uuid4().hex}", display_name="Assessment Student",
        role="student", password_hash=hash_password("assessment student password"), must_change_password=False)
    session.add_all([parent_user, student_user]); session.flush()
    session.add_all([StudentProfile(student_id=student_user.id, parent_id=parent_user.id),
        StudentProgression(student_id=student_user.id, course_id="igcse", grade=10, term=1, is_current=True),
        StudentSubject(student_id=student_user.id, subject_id="biology")])
    plan = CurriculumPlan(course_id="igcse", subject_id="biology", textbook_content_version_id=content.id,
        version_number=1, status="published", created_by=admin.id, published_by=admin.id)
    session.add(plan); session.flush()
    session.add_all([CurriculumPlanUnit(plan_id=plan.id, grade=10, term=1, unit_id=unit.id) for unit in biology_units])
    session.commit()

    blueprint = client.post("/api/v1/assessments/admin/blueprints", headers=csrf, json={
        "name": "Biology Term 1 mock", "subjectId": "biology", "grade": 10, "term": 1,
        "targetMarks": 2, "durationMinutes": 30, "questionCount": 1,
        "skills": ["application"], "difficultyProfile": {"mixed": 1},
    })
    assert blueprint.status_code == 201, blueprint.text
    shortage_blueprint = client.post("/api/v1/assessments/admin/blueprints", headers=csrf, json={
        "name": "Impossible mock", "subjectId": "biology", "grade": 10, "term": 1,
        "targetMarks": 99, "durationMinutes": 30, "questionCount": 1,
        "skills": [], "difficultyProfile": {"mixed": 1},
    }).json()
    student_login = client.post("/api/v1/auth/login", json={
        "username": student_user.username, "password": "assessment student password",
    }).json()
    student_csrf = {"X-CSRF-Token": student_login["csrfToken"]}
    shortage = client.post("/api/v1/assessments/start", headers=student_csrf, json={
        "mode": "mock", "subjectId": "biology", "blueprintId": shortage_blueprint["id"],
    })
    assert shortage.status_code == 409 and shortage.json()["error"]["code"] == "question_pool_shortage"
    started = client.post("/api/v1/assessments/start", headers=student_csrf, json={
        "mode": "mock", "subjectId": "biology", "blueprintId": blueprint.json()["id"],
    })
    assert started.status_code == 201, started.text
    exam = started.json(); frozen = exam["questions"][0]
    assert frozen["rubric"] is None and exam["feedbackVisible"] is False
    assert client.post("/api/v1/assessments/start", headers=student_csrf, json={
        "mode": "practice", "subjectId": "biology",
    }).status_code == 409
    source_question = session.get(OfficialQuestionVersion, uuid.UUID(frozen["id"]))
    assert source_question is None  # Public IDs identify frozen snapshots, not source questions.
    snapshot_row = session.get(AssessmentQuestion, uuid.UUID(frozen["id"]))
    original_prompt = snapshot_row.prompt
    session.get(OfficialQuestionVersion, snapshot_row.source_question_version_id).prompt = "Edited after start"
    session.commit()
    assert client.get("/api/v1/assessments").json()["assessments"][0]["questions"][0]["prompt"] == original_prompt
    save_payload = {"questionId": frozen["id"], "answer": "Cell membrane", "idempotencyKey": "save-answer-0001"}
    arbitrary = client.post(f"/api/v1/assessments/{exam['id']}/answers", headers=student_csrf, json={
        "questionId": second_question["questionId"], "answer": "client-selected", "idempotencyKey": "bad-answer-0001"})
    assert arbitrary.status_code == 404
    first_save = client.post(f"/api/v1/assessments/{exam['id']}/answers", headers=student_csrf, json=save_payload)
    retry_save = client.post(f"/api/v1/assessments/{exam['id']}/answers", headers=student_csrf, json=save_payload)
    assert first_save.json()["questions"][0]["saveRevision"] == retry_save.json()["questions"][0]["saveRevision"] == 1
    submitted = client.post(f"/api/v1/assessments/{exam['id']}/submit", headers=student_csrf,
        json={"idempotencyKey": "submit-exam-0001"})
    repeated = client.post(f"/api/v1/assessments/{exam['id']}/submit", headers=student_csrf,
        json={"idempotencyKey": "submit-exam-0001"})
    assert submitted.status_code == repeated.status_code == 200
    assert submitted.json()["feedbackVisible"] is True and submitted.json()["questions"][0]["rubric"] is not None

    marking_calls = []
    def fake_marking(db, settings, request):
        payload = json.loads(request.task); marking_calls.append(request)
        decisions = [{"pointId": point["pointId"], "criterion": point["criterion"], "awarded": True,
            "marksAwarded": point["maxMarks"], "maxMarks": point["maxMarks"],
            "studentEvidence": "Cell membrane", "rationale": "The answer states the required structure.", "confidence": 0.94}
            for point in payload["officialMarkingPoints"]]
        output = ({"decisions": decisions, "overallConfidence": 0.94, "reviewReasons": []}
            if request.output_type.__name__ == "AssessmentPassOne" else
            {"decisions": decisions, "strengths": ["Correctly named the membrane."], "smallMistakes": [],
             "conceptualMistakes": [], "improvedAnswer": "A cell has a cell membrane.",
             "teachingExplanation": "The membrane controls movement into and out of the cell.",
             "unitEvidence": [{"unitId": frozen["unitIds"][0], "evidence": "The response identifies a cell structure."}],
             "recommendations": ["Revise the functions of cell structures."], "confidence": 0.94, "reviewReasons": []})
        return AIResult(output=request.output_type.model_validate(output), provider="fake", model="fake-assessor-v1",
            response_id=f"response-{len(marking_calls)}", usage=AIUsage(), latency_ms=1, attempt_count=1)
    monkeypatch.setattr(assessment_marking, "_generate", fake_marking)
    evaluation_corpus = EvaluationCorpus(subject_id="biology", version_number=1, name="Reviewed biology corpus",
        cases=[], status="approved", content_hash="a" * 64, created_by=admin.id, approved_by=admin.id, approved_at=datetime.now(timezone.utc))
    session.add(evaluation_corpus); session.flush()
    evaluation_run = EvaluationRun(corpus_id=evaluation_corpus.id, subject_id="biology", candidate_model="fake-assessor-v1",
        prompt_version="2.0.0", observations_hash="b" * 64, metrics={}, thresholds={}, passed=True,
        failure_reasons=[], created_by=admin.id)
    session.add(evaluation_run); session.flush()
    session.add(EvaluationRelease(subject_id="biology", workflow="assessment_feedback", mode="automatic",
        run_id=evaluation_run.id, confidence_threshold=.85, activated_by=admin.id))
    session.commit()
    assessed = client.post(f"/api/v1/assessments/{exam['id']}/evaluate", headers=student_csrf,
        json={"idempotencyKey": "evaluate-exam-0001"})
    assert assessed.status_code == 200, assessed.text
    result = assessed.json()["questions"][0]["result"]
    assert result["awardedMarks"] <= result["maxMarks"] and result["status"] == "published"
    usage = session.query(FamilyUsageEvent).filter_by(student_id=student_user.id).all()
    assert {(row.kind, row.quantity) for row in usage} == {("ai_request", 2), ("ai_token", 0)}
    assert result["markingDecisions"][0]["studentEvidence"] == "Cell membrane"
    mastery_rows = session.query(UnitMastery).filter_by(student_id=student_user.id).order_by(UnitMastery.unit_id).all()
    assert len(mastery_rows) == 2 and all(row.confidence == "low" and row.provisional for row in mastery_rows)
    assert sorted(round(float(row.evidence_weight), 2) for row in mastery_rows) == [0.64, 0.96]
    assert session.query(UnitMasteryDimension).count() == 14
    assert session.query(UnitMasteryEvent).count() == 2
    mastery_api = client.get(f"/api/v1/mastery/students/{student_user.id}")
    assert mastery_api.status_code == 200 and len(mastery_api.json()["units"]) == 2
    expected_mastery = result["awardedMarks"] / result["maxMarks"] * 10
    assert all(unit["score"] == expected_mastery and unit["preciseScore"] == expected_mastery for unit in mastery_api.json()["units"])
    first_row = session.query(AssessmentResult).filter_by(assessment_id=uuid.UUID(exam["id"])).one()
    for index, unit in enumerate(biology_units):
        session.add(RetrievalChunk(document_id=textbook.id, document_version_id=textbook_file.id,
            textbook_content_version_id=content.id, official_material_version_id=None, unit_id=unit.id,
            course_id="igcse", subject_id="biology", source_type="textbook_section", source_item_id=uuid.uuid4(),
            source_ordinal=index, content=f"Approved explanation for {unit.title}.", page_number=index + 1,
            bounding_box={}, content_hash=uuid.uuid4().hex * 2, embedding_model="test", embedding_version=1,
            embedding=embed_texts(Settings(database_password="test", embedding_provider="local"), [unit.title])[0], status="active"))
    first_row.small_mistakes = ["Use the correct scientific terminology."]
    session.commit(); weaknesses.record_result(session, first_row)
    diagnoses = session.query(WeaknessDiagnosis).filter_by(student_id=student_user.id).all()
    recommendations = session.query(ImprovementRecommendation).filter_by(student_id=student_user.id).all()
    assert len(diagnoses) == 2 and all(row.category == "terminology" and row.occurrence_number == 1 for row in diagnoses)
    assert len(recommendations) == 8 and {row.activity_type for row in recommendations} == {"review", "targeted_practice", "spaced_retry", "unit_check"}
    assert all(row.review_status == "pending_review" and row.source_chunk_id for row in recommendations)
    eligible_ids = {row[0].id for row in assessments.eligible_questions(session, student_user.id, "biology")}
    assert all(row.activity_question_version_id in eligible_ids for row in recommendations if row.activity_question_version_id)
    assert client.get("/api/v1/recommendations").json()["recommendations"] == []
    assert first_row.rubric_snapshot and first_row.prompt_version == "2.0.0"
    assert {source["type"] for source in first_row.source_manifest} >= {"frozen_question", "frozen_rubric"}
    assert client.post(f"/api/v1/assessments/{exam['id']}/evaluate", headers=student_csrf,
        json={"idempotencyKey": "evaluate-exam-0001"}).status_code == 200
    assert session.query(AssessmentResult).filter_by(assessment_id=uuid.UUID(exam["id"])).count() == 1
    assert client.post(f"/api/v1/assessments/{exam['id']}/evaluate", headers=student_csrf,
        json={"idempotencyKey": "evaluate-exam-0002"}).status_code == 200
    assert [row.version_number for row in session.query(AssessmentResult).filter_by(
        assessment_id=uuid.UUID(exam["id"])).order_by(AssessmentResult.version_number)] == [1, 2]
    assert all(row.evidence_count == 1 and row.version_number == 2 for row in session.query(UnitMastery).all())
    assert session.query(UnitMasteryEvent).count() == 4

    official = client.post("/api/v1/assessments/start", headers=student_csrf, json={
        "mode": "official_paper", "subjectId": "biology", "paperId": paper_id,
    })
    assert official.status_code == 201 and len(official.json()["questions"]) == 2
    official_row = session.get(Assessment, uuid.UUID(official.json()["id"]))
    official_row.ends_at = datetime.now(timezone.utc) - timedelta(seconds=1); session.commit()
    late_save = client.post(f"/api/v1/assessments/{official.json()['id']}/answers", headers=student_csrf, json={
        "questionId": official.json()["questions"][0]["id"], "answer": "late edit", "idempotencyKey": "late-answer-0001"})
    assert late_save.status_code == 409
    expired_submit = client.post(f"/api/v1/assessments/{official.json()['id']}/submit", headers=student_csrf,
        json={"idempotencyKey": "submit-late-0001"})
    assert expired_submit.status_code == 200 and expired_submit.json()["status"] == "expired"
    assert expired_submit.json()["feedbackVisible"] is True
    practice = client.post("/api/v1/assessments/start", headers=student_csrf, json={
        "mode": "practice", "subjectId": "biology",
    })
    assert practice.status_code == 201 and len(practice.json()["questions"]) == 1
    practice_data = practice.json(); practice_question = practice_data["questions"][0]
    hint = client.post(f"/api/v1/assessments/{practice_data['id']}/questions/{practice_question['id']}/hint",
        headers=student_csrf, json={"idempotencyKey": "practice-hint-0001"})
    assert hint.status_code == 200 and hint.json()["total"] == 3
    monkeypatch.setattr(assessment_working, "extract_document", lambda *args, **kwargs: {"pageCount": 1, "pages": [{
        "blocks": [{"text": "cell membrane", "confidence": 0.72}]}]})
    working = client.post(f"/api/v1/assessments/{practice_data['id']}/questions/{practice_question['id']}/working",
        headers={**student_csrf, "X-Filename": "working.png", "Content-Type": "image/png"},
        content=b"\x89PNG\r\n\x1a\nreviewed-test-image")
    assert working.status_code == 201, working.text
    assert working.json()["ocrConfidence"] == 0.72 and working.json()["needsReview"] is True
    assert client.get(f"/api/v1/assessments/{practice_data['id']}/working/{working.json()['id']}").content.startswith(b"\x89PNG")
    assert client.post(f"/api/v1/assessments/{practice_data['id']}/answers", headers=student_csrf, json={
        "questionId": practice_question["id"], "answer": "", "fileId": working.json()["id"],
        "idempotencyKey": "working-answer-0001"}).status_code == 200
    assert client.post(f"/api/v1/assessments/{practice_data['id']}/submit", headers=student_csrf,
        json={"idempotencyKey": "working-submit-0001"}).status_code == 200
    reviewed = client.post(f"/api/v1/assessments/{practice_data['id']}/evaluate", headers=student_csrf,
        json={"idempotencyKey": "working-evaluate-0001"})
    assert reviewed.status_code == 200, reviewed.text
    assert reviewed.json()["questions"][0]["result"]["status"] == "needs_review"
    assert "inspect the original image" in reviewed.json()["questions"][0]["result"]["reviewReasons"][0]
    parent_login = client.post("/api/v1/auth/login", json={
        "username": parent_user.username, "password": "assessment parent password"})
    assert parent_login.status_code == 200
    parent_csrf = {"X-CSRF-Token": parent_login.json()["csrfToken"]}
    pending_recommendations = client.get(f"/api/v1/recommendations?studentId={student_user.id}")
    assert pending_recommendations.status_code == 200 and len(pending_recommendations.json()["recommendations"]) == 8
    reviewed_recommendation = client.post(f"/api/v1/recommendations/{recommendations[0].id}/review", headers=parent_csrf,
        json={"decision": "approved", "reason": "Suitable for this child."})
    assert reviewed_recommendation.status_code == 200 and reviewed_recommendation.json()["reviewStatus"] == "approved"
    assert client.get(f"/api/v1/mastery/students/{student_user.id}").status_code == 200
    working_url = f"/api/v1/assessments/{practice_data['id']}/working/{working.json()['id']}"
    assert client.get(working_url).status_code == 200
    first_plan = client.get(f"/api/v1/plans/students/{student_user.id}")
    assert first_plan.status_code == 200 and first_plan.json()["generationReason"] == "evidence"
    assert len(first_plan.json()["items"]) == 1
    planned = first_plan.json()["items"][0]
    assert planned["subject"] == "biology" and uuid.UUID(planned["unitId"]) in {unit.id for unit in biology_units}
    assert planned["reason"] and planned["source"] == reviewed_recommendation.json()["sourceTitle"] + " · page " + str(reviewed_recommendation.json()["sourcePage"])
    assert planned["successCondition"] and planned["minutes"] >= 5
    unchanged = client.get(f"/api/v1/plans/students/{student_user.id}")
    assert unchanged.json()["id"] == first_plan.json()["id"]
    requested = client.post("/api/v1/plans", headers=parent_csrf, json={"studentId": str(student_user.id)})
    assert requested.status_code == 200 and requested.json()["version"] == 2
    student_login_again = client.post("/api/v1/auth/login", json={"username": student_user.username, "password": "assessment student password"}).json()
    student_csrf_again = {"X-CSRF-Token": student_login_again["csrfToken"]}
    completed = client.post(f"/api/v1/plans/items/{requested.json()['items'][0]['id']}/complete", headers=student_csrf_again, json={})
    assert completed.status_code == 200 and completed.json()["items"][0]["status"] == "completed"
    regenerated = client.post("/api/v1/plans", headers=student_csrf_again, json={})
    assert regenerated.status_code == 200 and regenerated.json()["version"] == 3
    history = client.get(f"/api/v1/plans/students/{student_user.id}/history")
    assert history.status_code == 200 and len(history.json()["plans"]) == 3
    assert any(item["status"] == "completed" for plan in history.json()["plans"] for item in plan["items"])
    assert session.query(StudyPlan).filter_by(student_id=student_user.id).count() == 3
    assert session.query(StudyPlanItem).filter_by(student_id=student_user.id).count() == 3
    # Step 18: media always starts from approved, same-subject indexed evidence.
    source_chunk = session.query(RetrievalChunk).filter_by(subject_id="biology").first()
    admin_login = client.post("/api/v1/auth/login", json={"username": username, "password": password}).json()
    admin_csrf = {"X-CSRF-Token": admin_login["csrfToken"]}
    deterministic = client.post("/api/v1/media/admin/deterministic", headers=admin_csrf, json={
        "kind":"plot_svg","subjectId":"biology","sourceChunkId":str(source_chunk.id),"title":"Diffusion graph",
        "altText":"A plotted line showing particle diffusion increasing over time.","parameters":{"points":[[0,0],[1,2],[2,3]]}})
    assert deterministic.status_code == 201, deterministic.text
    assert deterministic.json()["status"] == "published" and deterministic.json()["provider"] == "akuru"
    class FakeImageRouter:
        def __init__(self,*_args,**_kwargs): pass
        def generate(self,_prompt,_operation_id):
            return SimpleNamespace(content=b"\x89PNG\r\n\x1a\nconcept",content_type="image/png",provider="openai",
                model="fake-image-v1",response_id="image-response")
    monkeypatch.setattr("app.services.media.ImageAccountRouter",FakeImageRouter)
    illustration = client.post("/api/v1/media/admin/illustrations", headers=admin_csrf, json={
        "subjectId":"biology","sourceChunkId":str(source_chunk.id),"title":"Cell membrane concept",
        "altText":"A conceptual view of particles crossing a cell membrane.",
        "prompt":"Illustrate particles moving across a cell membrane without adding answer labels."})
    assert illustration.status_code == 201, illustration.text
    assert illustration.json()["status"] == "pending_review"
    assert session.get(EducationalMedia,uuid.UUID(illustration.json()["id"])).source_manifest[0]["contentHash"] == source_chunk.content_hash
    student_login = client.post("/api/v1/auth/login", json={"username": student_user.username, "password":"assessment student password"}).json()
    media_scope=f"?studentId={student_user.id}&subjectId=biology"
    visible=client.get("/api/v1/media"+media_scope)
    assert visible.status_code == 200 and [row["id"] for row in visible.json()["media"]] == [deterministic.json()["id"]]
    assert visible.json()["media"][0]["prompt"] == "" and visible.json()["media"][0]["parameters"] == {}
    assert client.get(f"/api/v1/media/{illustration.json()['id']}/content?studentId={student_user.id}").status_code == 404
    admin_login = client.post("/api/v1/auth/login", json={"username": username, "password": password}).json()
    admin_csrf={"X-CSRF-Token":admin_login["csrfToken"]}
    published=client.post(f"/api/v1/media/admin/{illustration.json()['id']}/review",headers=admin_csrf,
        json={"decision":"published","notes":"Compared with the approved cell membrane section."})
    assert published.status_code == 200 and published.json()["status"] == "published"
    assert session.query(AuditEvent).filter_by(action="media.review",target_id=illustration.json()["id"]).one()
    student_login=client.post("/api/v1/auth/login",json={"username":student_user.username,"password":"assessment student password"}).json()
    assert client.get(f"/api/v1/media/{illustration.json()['id']}/content?studentId={student_user.id}").content.startswith(b"\x89PNG")
    assert len(client.get("/api/v1/media"+media_scope).json()["media"]) == 2
    assert client.post("/api/v1/media/admin/deterministic",headers={"X-CSRF-Token":student_login["csrfToken"]},json={
        "kind":"forces_svg","subjectId":"biology","sourceChunkId":str(source_chunk.id),"title":"Forces",
        "altText":"Two labelled forces act on an object.","parameters":{}}).status_code == 403
    admin_login=client.post("/api/v1/auth/login",json={"username":username,"password":password}).json()
    assert client.post("/api/v1/media/admin/deterministic",headers={"X-CSRF-Token":admin_login["csrfToken"]},json={
        "kind":"forces_svg","subjectId":"physics","sourceChunkId":str(source_chunk.id),"title":"Forces",
        "altText":"Two labelled forces act on an object.","parameters":{}}).status_code == 409
    parent_login=client.post("/api/v1/auth/login",json={"username":parent_user.username,"password":"assessment parent password"}).json()
    assert client.get(f"/api/v1/media/{illustration.json()['id']}/content?studentId={student_user.id}").status_code == 200
    unrelated_parent = User(username=f"unrelated-parent-{uuid.uuid4().hex}", display_name="Unrelated Parent",
        role="parent", password_hash=hash_password("unrelated parent password"), must_change_password=False)
    session.add(unrelated_parent); session.commit()
    assert client.post("/api/v1/auth/login", json={"username": unrelated_parent.username,
        "password": "unrelated parent password"}).status_code == 200
    assert client.get(working_url).status_code == 404
    assert client.get(f"/api/v1/mastery/students/{student_user.id}").status_code == 403
    assert client.get(f"/api/v1/recommendations?studentId={student_user.id}").status_code == 403
    assert client.get(f"/api/v1/plans/students/{student_user.id}").status_code == 403
    assert client.get("/api/v1/media"+media_scope).status_code == 403
    assert client.get(f"/api/v1/media/{illustration.json()['id']}/content?studentId={student_user.id}").status_code == 404

    # Step 17: the new state path and review endpoints preserve family boundaries.
    assert client.get("/api/v1/state").json()["attempts"] == []
    review_result = reviewed.json()["questions"][0]["result"]
    review_url = f"/api/v1/assessments/results/{review_result['id']}/review"
    review_payload = {"idempotencyKey": "human-review-0001", "markingDecisions": review_result["markingDecisions"],
        "feedback": "Reviewed against the original working and rubric.", "improvedAnswer": review_result["improvedAnswer"],
        "strengths": ["Identified a membrane."], "smallMistakes": [], "conceptualMistakes": [], "reason": "Verified original working."}
    login = client.post("/api/v1/auth/login", json={"username": unrelated_parent.username, "password": "unrelated parent password"}).json()
    unrelated_csrf = {"X-CSRF-Token": login["csrfToken"]}
    assert client.post(review_url, headers=unrelated_csrf, json=review_payload).status_code == 404
    assert client.get("/api/v1/assessments/admin/audit").status_code == 403
    login = client.post("/api/v1/auth/login", json={"username": student_user.username, "password": "assessment student password"}).json()
    assert client.post(review_url, headers={"X-CSRF-Token": login["csrfToken"]}, json=review_payload).status_code == 403
    assert client.get("/api/v1/assessments/admin/audit").status_code == 403
    login = client.post("/api/v1/auth/login", json={"username": parent_user.username, "password": "assessment parent password"}).json()
    review_csrf = {"X-CSRF-Token": login["csrfToken"]}
    state = client.get("/api/v1/state").json()
    assert state["attempts"] and all(item["studentId"] == str(student_user.id) for item in state["attempts"])
    assert client.post(review_url, json=review_payload).status_code == 403
    bad_payload = {**review_payload, "markingDecisions": [{**review_payload["markingDecisions"][0], "criterion": "Invented criterion"}]}
    assert client.post(review_url, headers=review_csrf, json=bad_payload).status_code == 422
    published_review = client.post(review_url, headers=review_csrf, json=review_payload)
    assert published_review.status_code == 200, published_review.text
    assert published_review.json()["status"] == "published"
    assert published_review.json()["version"] == review_result["version"] + 1
    assert client.post(review_url, headers=review_csrf, json=review_payload).json()["id"] == published_review.json()["id"]
    assert client.post(review_url, headers=review_csrf, json={**review_payload, "idempotencyKey": "human-review-0002"}).status_code == 409
    session.expire_all()
    persisted = session.get(AssessmentResult, uuid.UUID(published_review.json()["id"]))
    assert persisted.source_manifest[-1]["type"] == "human_review"
    assert session.get(AssessmentResult, uuid.UUID(review_result["id"])).status == "needs_review"
    admin_login = client.post("/api/v1/auth/login", json={"username": username, "password": password}).json()
    admin_csrf = {"X-CSRF-Token": admin_login["csrfToken"]}
    audit = client.get("/api/v1/assessments/admin/audit")
    assert audit.status_code == 200 and any(row["resultId"] == published_review.json()["id"] for row in audit.json()["results"])
    reassess_url = f"/api/v1/assessments/admin/{practice_data['id']}/reassess"
    assert client.post(reassess_url, json={"idempotencyKey": "admin-reassess-0001"}).status_code == 403
    reassessed = client.post(reassess_url, headers=admin_csrf, json={"idempotencyKey": "admin-reassess-0001"})
    assert reassessed.status_code == 200, reassessed.text
    new_result = reassessed.json()["questions"][0]["result"]
    assert new_result["version"] == published_review.json()["version"] + 1
    assert client.post(reassess_url, headers=admin_csrf, json={"idempotencyKey": "admin-reassess-0001"}).json()["questions"][0]["result"]["id"] == new_result["id"]
    session.expire_all()
    assert session.get(AssessmentResult, uuid.UUID(new_result["id"])).status == "needs_review"
    assert client.get(working_url).status_code == 200
    admin_review_payload = {**review_payload, "idempotencyKey": "admin-review-0001",
        "markingDecisions": [{**point, "awarded": False, "marksAwarded": 0, "rationale": "The required evidence is absent."} for point in new_result["markingDecisions"]]}
    corrected = client.post(f"/api/v1/assessments/results/{new_result['id']}/review", headers=admin_csrf, json=admin_review_payload)
    assert corrected.status_code == 200, corrected.text
    assert corrected.json()["awardedMarks"] == 0 and corrected.json()["version"] == new_result["version"] + 1
    assert session.query(AuditEvent).filter_by(action="assessment.review", target_id=corrected.json()["id"]).one().actor_id == uuid.UUID(admin_login["user"]["id"])


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
        {"caseId": "mapping", "category": "mapping", "expected": {"unitIds": ["u1"], "crossSubjectRejected": True}},
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
        "diagram": {"preserved": True}, "mapping": {"unitIds": ["u1"], "crossSubjectRejected": True},
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
    assert client.post("/api/v1/evaluations/admin/corpora", json={"subjectId": "maths", "name": "Denied", "cases": cases}).status_code == 403
