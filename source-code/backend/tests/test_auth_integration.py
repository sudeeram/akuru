import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import engine, get_db
from app.main import app
from app.models import AuditEvent, StudentProfile, StudentProgression, StudentSubject, User
from app.security import hash_password


@pytest.fixture
def auth_client():
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

    app.dependency_overrides[get_db] = override_db
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
    assert response.json() == {"detail": "Origin not allowed."}


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
        issue["loc"][-1] == "password" and "at least 12 characters" in issue["msg"]
        for issue in invalid_parent.json()["detail"]
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
    assert reused.json()["detail"] == "The new password cannot be same as the existing password."
    response = client.post("/api/v1/auth/change-password", headers={"X-CSRF-Token": user_login["csrfToken"]}, json={
        "newPassword": "a completely new secure password",
    })
    assert response.status_code == 204
    assert client.get("/api/v1/auth/me").json()["mustChangePassword"] is False
