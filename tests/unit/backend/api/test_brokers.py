"""Tests for /api/brokers/* endpoints."""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


def test_brokers_fyers_status_not_connected(backend_app, monkeypatch):
    """Test Fyers status when not connected."""
    monkeypatch.setenv("API_KEY", "test-api-key-32-chars-long-enough")

    # Mock get_settings to return a settings object with no token
    from fyers_hub.auth.store import Token
    import backend.api.brokers as brokers_mod

    mock_settings = MagicMock()
    mock_settings.token_path = "/tmp/nonexistent_token.json"
    mock_settings.require_app = MagicMock()

    with patch("backend.api.brokers.get_settings", return_value=mock_settings):
        with patch("backend.api.brokers.load_token", return_value=None):
            from backend.app import create_app
            app = create_app()
            client = TestClient(app)

            response = client.get("/brokers/fyers/status", headers={"X-API-Key": "test-api-key-32-chars-long-enough"})
            assert response.status_code == 200
            data = response.json()
            assert data["broker"] == "fyers"
            assert data["connected"] is False
            assert data["error"] == "Not connected or token expired"


def test_brokers_fyers_status_connected(backend_app, monkeypatch):
    """Test Fyers status when connected with valid token."""
    monkeypatch.setenv("API_KEY", "test-api-key-32-chars-long-enough")

    import time
    from fyers_hub.auth.store import Token

    mock_settings = MagicMock()
    mock_settings.token_path = "/tmp/token.json"
    mock_settings.require_app = MagicMock()

    # Token valid for 10 hours
    tok = Token(
        access_token="test_access",
        refresh_token="test_refresh",
        app_id="test_app",
        issued_at=int(time.time()),
        expires_at=int(time.time()) + 36000,
    )

    with patch("backend.api.brokers.get_settings", return_value=mock_settings):
        with patch("backend.api.brokers.load_token", return_value=tok):
            from backend.app import create_app
            app = create_app()
            client = TestClient(app)

            response = client.get("/brokers/fyers/status", headers={"X-API-Key": "test-api-key-32-chars-long-enough"})
            assert response.status_code == 200
            data = response.json()
            assert data["broker"] == "fyers"
            assert data["connected"] is True
            assert data["expires_at"] == tok.expires_at
            assert data["expires_in_hours"] in (9, 10)


def test_brokers_fyers_auth_url(backend_app, monkeypatch):
    """Test getting Fyers auth URL."""
    monkeypatch.setenv("API_KEY", "test-api-key-32-chars-long-enough")

    mock_settings = MagicMock()
    mock_settings.require_app = MagicMock()
    mock_settings.app_id = "test_app_id"
    mock_settings.redirect_uri = "http://localhost/callback"
    mock_settings.home = MagicMock()
    mock_settings.home.mkdir = MagicMock()

    with patch("backend.api.brokers.get_settings", return_value=mock_settings):
        with patch("backend.api.brokers.flow.login_url", return_value="https://fyers.in/auth?code=123"):
            from backend.app import create_app
            app = create_app()
            client = TestClient(app)

            response = client.get("/brokers/fyers/auth-url", headers={"X-API-Key": "test-api-key-32-chars-long-enough"})
            assert response.status_code == 200
            assert response.json()["auth_url"] == "https://fyers.in/auth?code=123"


def test_brokers_fyers_connect_success(backend_app, monkeypatch):
    """Test successful Fyers connect."""
    monkeypatch.setenv("API_KEY", "test-api-key-32-chars-long-enough")

    mock_settings = MagicMock()
    mock_settings.require_app = MagicMock()

    with patch("backend.api.brokers.get_settings", return_value=mock_settings):
        with patch("backend.api.brokers.flow.parse_auth_code", return_value="auth_code_123"):
            with patch("backend.api.brokers.flow.exchange_code") as mock_exchange:
                mock_exchange.return_value = MagicMock()
                from backend.app import create_app
                app = create_app()
                client = TestClient(app)

                response = client.post(
                    "/brokers/fyers/connect",
                    json={"redirect_url": "http://localhost/callback?auth_code=123&state=abc"},
                    headers={"X-API-Key": "test-api-key-32-chars-long-enough"}
                )
                assert response.status_code == 200
                assert response.json()["ok"] is True
                assert "connected successfully" in response.json()["message"]


def test_brokers_fyers_connect_invalid_code(backend_app, monkeypatch):
    """Test Fyers connect with invalid auth code."""
    monkeypatch.setenv("API_KEY", "test-api-key-32-chars-long-enough")

    mock_settings = MagicMock()
    mock_settings.require_app = MagicMock()

    from fyers_hub.auth.flow import AuthError

    with patch("backend.api.brokers.get_settings", return_value=mock_settings):
        with patch("backend.api.brokers.flow.parse_auth_code", side_effect=AuthError("Invalid code")):
            from backend.app import create_app
            app = create_app()
            client = TestClient(app)

            response = client.post(
                "/brokers/fyers/connect",
                json={"redirect_url": "http://localhost/callback?auth_code=invalid"},
                headers={"X-API-Key": "test-api-key-32-chars-long-enough"}
            )
            assert response.status_code == 400
            assert "Invalid code" in response.json()["detail"]


def test_brokers_fyers_refresh_success(backend_app, monkeypatch):
    """Test successful token refresh."""
    monkeypatch.setenv("API_KEY", "test-api-key-32-chars-long-enough")

    import time
    from fyers_hub.auth.store import Token

    mock_settings = MagicMock()
    mock_settings.require_app = MagicMock()

    new_tok = Token(
        access_token="new_access",
        refresh_token="test_refresh",
        app_id="test_app",
        issued_at=int(time.time()),
        expires_at=int(time.time()) + 36000,
    )

    with patch("backend.api.brokers.get_settings", return_value=mock_settings):
        with patch("backend.api.brokers.flow.refresh", return_value=new_tok):
            from backend.app import create_app
            app = create_app()
            client = TestClient(app)

            response = client.post(
                "/brokers/fyers/refresh",
                headers={"X-API-Key": "test-api-key-32-chars-long-enough"}
            )
            assert response.status_code == 200
            assert response.json()["ok"] is True
            assert response.json()["expires_at"] == new_tok.expires_at


def test_brokers_fyers_refresh_needs_login(backend_app, monkeypatch):
    """Test refresh when refresh token is missing."""
    monkeypatch.setenv("API_KEY", "test-api-key-32-chars-long-enough")

    mock_settings = MagicMock()
    mock_settings.require_app = MagicMock()

    from fyers_hub.auth.flow import NeedsLogin

    with patch("backend.api.brokers.get_settings", return_value=mock_settings):
        with patch("backend.api.brokers.flow.refresh", side_effect=NeedsLogin("refresh_token nahi hai")):
            from backend.app import create_app
            app = create_app()
            client = TestClient(app)

            response = client.post(
                "/brokers/fyers/refresh",
                headers={"X-API-Key": "test-api-key-32-chars-long-enough"}
            )
            assert response.status_code == 400
            assert "refresh_token nahi hai" in response.json()["detail"]


def test_brokers_fyers_disconnect(backend_app, monkeypatch):
    """Test Fyers disconnect deletes token file."""
    monkeypatch.setenv("API_KEY", "test-api-key-32-chars-long-enough")

    mock_settings = MagicMock()
    mock_settings.require_app = MagicMock()
    mock_token_path = MagicMock()
    mock_token_path.exists.return_value = True
    mock_settings.token_path = mock_token_path

    with patch("backend.api.brokers.get_settings", return_value=mock_settings):
        from backend.app import create_app
        app = create_app()
        client = TestClient(app)

        response = client.post(
            "/brokers/fyers/disconnect",
            headers={"X-API-Key": "test-api-key-32-chars-long-enough"}
        )
        assert response.status_code == 200
        assert response.json()["ok"] is True
        assert "disconnected" in response.json()["message"]
        mock_token_path.unlink.assert_called_once()


def test_brokers_token_not_in_response(backend_app, monkeypatch):
    """Test that tokens are never returned in API responses."""
    monkeypatch.setenv("API_KEY", "test-api-key-32-chars-long-enough")

    import time
    from fyers_hub.auth.store import Token

    mock_settings = MagicMock()
    mock_settings.token_path = "/tmp/token.json"
    mock_settings.require_app = MagicMock()

    tok = Token(
        access_token="secret_access_token_12345",
        refresh_token="secret_refresh_token_67890",
        app_id="test_app",
        issued_at=int(time.time()),
        expires_at=int(time.time()) + 36000,
    )

    with patch("backend.api.brokers.get_settings", return_value=mock_settings):
        with patch("backend.api.brokers.load_token", return_value=tok):
            from backend.app import create_app
            app = create_app()
            client = TestClient(app)

            response = client.get("/brokers/fyers/status", headers={"X-API-Key": "test-api-key-32-chars-long-enough"})
            assert response.status_code == 200
            data = response.json()

            # Tokens should NOT be in response
            assert "access_token" not in data
            assert "refresh_token" not in data
            assert "secret_access_token_12345" not in str(data)
            assert "secret_refresh_token_67890" not in str(data)
            # Only safe fields
            assert data["connected"] is True
            assert data["expires_at"] == tok.expires_at


def test_brokers_unauthorized_without_auth(backend_app):
    """Test broker endpoints require authentication."""
    from backend.app import create_app
    app = create_app()
    client = TestClient(app)

    endpoints = [
        ("GET", "/brokers/fyers/status"),
        ("GET", "/brokers/fyers/auth-url"),
        ("POST", "/brokers/fyers/connect"),
        ("POST", "/brokers/fyers/refresh"),
        ("POST", "/brokers/fyers/disconnect"),
    ]

    for method, path in endpoints:
        if method == "GET":
            response = client.get(path)
        else:
            response = client.post(path, json={})
        assert response.status_code == 401, f"{method} {path} should require auth"