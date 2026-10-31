import os

import pytest

from cli.commands import make_sample_csv


def _client(tmp_path):
    try:
        from fastapi.testclient import TestClient
    except ImportError:
        pytest.skip("fastapi/httpx not installed")
    from backend.app import create_app
    make_sample_csv(tmp_path / "data" / "s.csv", days=20)
    os.environ["DATA_DIR"], os.environ["RUNS_ROOT"] = str(tmp_path / "data"), str(tmp_path / "runs")
    os.environ.pop("API_KEY", None)
    return TestClient(create_app())


def test_routes_and_errors(tmp_path):
    c = _client(tmp_path)
    assert c.get("/health").json() == {"status": "ok"}
    assert len(c.get("/strategies").json()) >= 2
    assert c.get("/strategies/unknown").status_code == 404
    assert c.get("/reports/run-nope").status_code == 404
    r = c.post("/backtests", json={"strategy_id": "three_pm_momentum", "dataset": "s.csv"})
    assert r.status_code == 200 and r.json()["status"] == "SUCCEEDED" and "x-request-id" in r.headers
    rid = r.json()["result"]["run_id"]
    assert c.get(f"/reports/{rid}").status_code == 200
    assert c.post("/comparisons", json={"run_ids": [rid]}).status_code == 400


def test_api_key_enforced(tmp_path):
    c = _client(tmp_path)
    os.environ["API_KEY"] = "secret"
    try:
        assert c.get("/health").status_code == 200
        assert c.get("/strategies").status_code == 401
        assert c.get("/strategies", headers={"x-api-key": "secret"}).status_code == 200
    finally:
        os.environ.pop("API_KEY", None)
