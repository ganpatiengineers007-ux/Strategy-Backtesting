
import pytest

from backend.api.audit import read_audit
from backend.api.health import health_payload


def test_payloads(tmp_path):
    assert health_payload() == {"status": "ok"}
    assert read_audit(str(tmp_path)) == []


def test_fastapi_app_routes():
    try:
        import fastapi  # noqa: F401
    except ImportError:
        pytest.skip("fastapi not installed")
    from backend.app import create_app
    paths = set(create_app().openapi()["paths"])
    assert {"/health", "/audit"} <= paths  # TODO: baaki 6 routes service layer ke baad
