import uuid
from contextlib import contextmanager

import pymupdf as fitz
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import engine, get_db
from app.main import app
from app.models import (
    AuditEvent, Document, DocumentAsset, DocumentBlock, DocumentEvent, DocumentJob,
    DocumentPage, DocumentVersion, StudentProfile,
    StudentProgression, StudentSubject, User,
)
from app.security import hash_password
from app.queue.factory import get_document_queue
from app.services import document_processing
from app.storage.factory import get_storage
from app.storage.local import LocalObjectStorage


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
    assert client.post("/api/v1/auth/login", json={"username": username, "password": "wrong-password"}).status_code == 401

    login = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert login.status_code == 200
    payload = login.json()
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
