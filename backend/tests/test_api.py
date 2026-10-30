from app.models.user import User, UserRole
from app.core.security import hash_password
from conftest import TestingSessionLocal


def register(client, email="student@example.com", password="StrongPassword123"):
    return client.post(
        "/api/auth/register",
        json={
            "full_name": "AIOps Student",
            "email": email,
            "password": password,
        },
    )


def login(client, email="student@example.com", password="StrongPassword123"):
    return client.post(
        "/api/auth/login",
        data={"username": email, "password": password},
    )


def test_health_endpoint_checks_database(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}


def test_registration_stores_hashed_password_and_defaults_to_viewer(client):
    response = register(client)
    assert response.status_code == 201
    assert response.json()["role"] == "viewer"
    assert "hashed_password" not in response.json()
    with TestingSessionLocal() as db:
        stored_user = db.query(User).filter_by(email="student@example.com").one()
        assert stored_user.hashed_password != "StrongPassword123"
        assert stored_user.hashed_password.startswith("$argon2")


def test_duplicate_registration_is_rejected(client):
    assert register(client).status_code == 201
    response = register(client)
    assert response.status_code == 409


def test_login_returns_token_and_me_is_protected(client):
    register(client)
    response = login(client)
    assert response.status_code == 200
    token = response.json()["access_token"]

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "student@example.com"


def test_invalid_password_is_rejected(client):
    register(client)
    response = login(client, password="IncorrectPassword123")
    assert response.status_code == 401


def test_protected_endpoints_require_authentication(client):
    for path in (
        "/api/auth/me",
        "/api/dashboard/overview",
        "/api/monitoring/resources",
        "/api/incidents",
        "/api/deployments",
        "/api/admin/users",
    ):
        assert client.get(path).status_code == 401


def test_viewer_cannot_access_admin_user_list(client):
    register(client)
    token = login(client).json()["access_token"]
    response = client.get("/api/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_admin_can_access_admin_user_list(client):
    register(client)
    with TestingSessionLocal() as db:
        admin = User(
            full_name="Admin",
            email="admin@example.com",
            hashed_password=hash_password("AdminPassword123"),
            role=UserRole.ADMIN,
        )
        db.add(admin)
        db.commit()

    token = login(client, "admin@example.com", "AdminPassword123").json()["access_token"]
    response = client.get("/api/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_registration_cannot_assign_admin_role(client):
    response = client.post(
        "/api/auth/register",
        json={
            "full_name": "AIOps Student",
            "email": "student@example.com",
            "password": "StrongPassword123",
            "role": "admin",
        },
    )
    assert response.status_code == 201
    assert response.json()["role"] == "viewer"


def test_dashboard_reports_empty_database_state(client):
    register(client)
    token = login(client).json()["access_token"]
    response = client.get(
        "/api/dashboard/overview",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["data_source"] == "database"
    assert response.json()["monitoring_connected"] is False
    assert response.json()["total_monitored_resources"] == 0
    assert response.json()["recent_activity"][0]["action"] == "user_registered"
