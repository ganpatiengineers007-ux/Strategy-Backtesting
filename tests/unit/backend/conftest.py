"""Pytest fixtures for backend tests."""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _reset_auth_state():
    """Reset shared session + limiter state before each test."""
    import backend.auth.session as session_mod
    session_mod.session_store._sessions.clear()
    session_mod.login_limiter._attempts.clear()
    session_mod.login_limiter._lockouts.clear()
    yield


def _create_app(monkeypatch, **env_vars):
    """Create a test FastAPI app with test settings."""
    # Disable rate limiting for tests
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "0")
    # Disable production checks
    monkeypatch.setenv("SVL_ENV", "development")
    # Set a default API key for tests that need it
    monkeypatch.setenv("API_KEY", "test-api-key-32-chars-long-enough")
    # Use temp database
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("HUB_DB_PATH", ":memory:")
    monkeypatch.setenv("JOB_STATE_DIR", "/tmp/test_jobs")

    # Apply any additional env vars
    for k, v in env_vars.items():
        monkeypatch.setenv(k, v)

    from backend.app import create_app
    app = create_app()
    return app


@pytest.fixture()
def backend_app(monkeypatch):
    """Create a test FastAPI app with default test settings."""
    return _create_app(monkeypatch)


@pytest.fixture()
def client(backend_app):
    """Test client for the backend app."""
    return TestClient(backend_app)


@pytest.fixture()
def make_app(monkeypatch):
    """Factory to create app with custom env vars."""
    def _make(**env_vars):
        return _create_app(monkeypatch, **env_vars)
    return _make