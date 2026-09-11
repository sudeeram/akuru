import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import engine, get_db
from app.main import app
from app.models import User
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
    }
    assert "password" not in login.text.lower()
    assert "HttpOnly" in login.headers["set-cookie"]
    assert "SameSite=strict" in login.headers["set-cookie"]

    assert client.get("/api/v1/auth/me").status_code == 200
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
