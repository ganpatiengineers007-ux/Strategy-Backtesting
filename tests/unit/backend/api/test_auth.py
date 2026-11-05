"""Tests for /auth/* endpoints."""
import bcrypt
import pytest
from fastapi.testclient import TestClient


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(12)).decode()


def test_auth_login_success(make_app):
    """Successful login returns HttpOnly SameSite=Strict cookie."""
    password = "testpassword123"
    app = make_app(ADMIN_USER="testadmin", ADMIN_PASSWORD_HASH=_hash(password))
    client = TestClient(app)

    response = client.post("/auth/login", json={"username": "testadmin", "password": password})
    assert response.status_code == 200
    assert response.json()["user"] == "testadmin"

    set_cookie = response.headers.get("set-cookie", "")
    assert "session_id=" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "samesite=strict" in set_cookie.lower()
    assert "Path=/" in set_cookie


def test_auth_login_wrong_password(make_app):
    """Wrong password returns 401 with remaining attempts."""
    password = "testpassword123"
    app = make_app(ADMIN_USER="testadmin", ADMIN_PASSWORD_HASH=_hash(password))
    client = TestClient(app)

    response = client.post("/auth/login", json={"username": "testadmin", "password": "wrongpassword"})
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]


def test_auth_login_unknown_user(make_app):
    """Unknown username returns 401."""
    app = make_app(ADMIN_USER="testadmin", ADMIN_PASSWORD_HASH=_hash("testpassword123"))
    client = TestClient(app)

    response = client.post("/auth/login", json={"username": "nobody", "password": "whatever12"})
    assert response.status_code == 401


def test_auth_login_lockout_after_5_failures(make_app):
    """Five failed attempts lock the IP+username for 15 minutes."""
    app = make_app(ADMIN_USER="testadmin", ADMIN_PASSWORD_HASH=_hash("testpassword123"))
    client = TestClient(app)

    for i in range(5):
        response = client.post("/auth/login", json={"username": "testadmin", "password": "wrong"})
        if i < 4:
            assert response.status_code == 401
        else:
            assert response.status_code == 429
            assert "Locked" in response.json()["detail"]

    # Lockout lasts 15 minutes
    from backend.auth.session import login_limiter
    locked, remaining = login_limiter.is_locked("testclient", "testadmin")
    assert locked
    assert 890 <= remaining <= 900

    # Even the correct password is rejected during lockout
    response = client.post("/auth/login", json={"username": "testadmin", "password": "testpassword123"})
    assert response.status_code == 429


def test_auth_me_with_cookie(make_app):
    """A valid session cookie authenticates /auth/me."""
    password = "testpassword123"
    app = make_app(ADMIN_USER="testadmin", ADMIN_PASSWORD_HASH=_hash(password))
    client = TestClient(app)

    login_resp = client.post("/auth/login", json={"username": "testadmin", "password": password})
    assert login_resp.status_code == 200

    response = client.get("/auth/me")
    assert response.status_code == 200
    assert response.json()["authenticated"] is True
    assert response.json()["user"] == "testadmin"


def test_auth_me_without_cookie(make_app):
    """Without a session /auth/me returns 401."""
    app = make_app()
    client = TestClient(app)

    response = client.get("/auth/me")
    assert response.status_code == 401


def test_api_requires_auth_without_session(make_app):
    """Protected API paths return 401 without a session (or X-API-Key)."""
    app = make_app()
    client = TestClient(app)

    for path in ("/api/strategies", "/api/datasets", "/api/brokers/fyers/status", "/strategies"):
        response = client.get(path)
        assert response.status_code == 401, f"{path} should require auth"


def test_health_is_public(make_app):
    """Health check works without login."""
    app = make_app()
    client = TestClient(app)

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_auth_logout(make_app):
    """Logout clears the session cookie and invalidates the session."""
    password = "testpassword123"
    app = make_app(ADMIN_USER="testadmin", ADMIN_PASSWORD_HASH=_hash(password))
    client = TestClient(app)

    login_resp = client.post("/auth/login", json={"username": "testadmin", "password": password})
    assert login_resp.status_code == 200

    response = client.post("/auth/logout")
    assert response.status_code == 200
    assert response.json()["ok"] is True

    set_cookie = response.headers.get("set-cookie", "")
    assert "session_id=" in set_cookie
    assert "Max-Age=0" in set_cookie or "Expires=" in set_cookie

    response = client.get("/auth/me")
    assert response.status_code == 401


def test_auth_login_audit_log(make_app, tmp_path):
    """Successful login is written to the audit log."""
    password = "testpassword123"
    app = make_app(ADMIN_USER="testadmin", ADMIN_PASSWORD_HASH=_hash(password), RUNS_ROOT=str(tmp_path))
    client = TestClient(app)

    client.post("/auth/login", json={"username": "testadmin", "password": password})

    from persistence import audit
    logs = audit.read(str(tmp_path))
    login_logs = [l for l in logs if l["event"] == "login_success"]
    assert len(login_logs) == 1
    assert login_logs[0]["username"] == "testadmin"
    assert login_logs[0]["success"] is True


def test_auth_failed_login_audit_log(make_app, tmp_path):
    """Failed login is written to the audit log."""
    app = make_app(ADMIN_USER="testadmin", ADMIN_PASSWORD_HASH=_hash("testpassword123"), RUNS_ROOT=str(tmp_path))
    client = TestClient(app)

    client.post("/auth/login", json={"username": "testadmin", "password": "wrong"})

    from persistence import audit
    logs = audit.read(str(tmp_path))
    failed_logs = [l for l in logs if l["event"] == "login_failed"]
    assert len(failed_logs) == 1
    assert failed_logs[0]["username"] == "testadmin"
    assert failed_logs[0]["success"] is False


def test_auth_logout_audit_log(make_app, tmp_path):
    """Logout is written to the audit log."""
    password = "testpassword123"
    app = make_app(ADMIN_USER="testadmin", ADMIN_PASSWORD_HASH=_hash(password), RUNS_ROOT=str(tmp_path))
    client = TestClient(app)

    client.post("/auth/login", json={"username": "testadmin", "password": password})
    client.post("/auth/logout")

    from persistence import audit
    logs = audit.read(str(tmp_path))
    logout_logs = [l for l in logs if l["event"] == "logout"]
    assert len(logout_logs) == 1
    assert logout_logs[0]["username"] == "testadmin"
    assert logout_logs[0]["success"] is True


def test_api_key_still_works(make_app):
    """X-API-Key still authenticates scripts/tests on protected endpoints."""
    app = make_app(API_KEY="test-api-key-32-chars-long-enough")
    client = TestClient(app)

    response = client.get("/strategies", headers={"X-API-Key": "test-api-key-32-chars-long-enough"})
    assert response.status_code == 200

    response = client.get("/strategies", headers={"X-API-Key": "wrong"})
    assert response.status_code == 401


def test_protected_endpoint_requires_auth(make_app):
    """A normal API endpoint is rejected without cookie or API key."""
    app = make_app(API_KEY="test-api-key-32-chars-long-enough")
    client = TestClient(app)

    response = client.get("/strategies")
    assert response.status_code == 401
