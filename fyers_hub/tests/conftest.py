import pytest

from fyers_hub.storage.db import connect


@pytest.fixture()
def conn():
    c = connect(":memory:")
    yield c
    c.close()


@pytest.fixture(autouse=True)
def _isolated_home(tmp_path, monkeypatch):
    monkeypatch.setenv("FYERS_HUB_HOME", str(tmp_path / "hub"))
    for k in ("FYERS_APP_ID", "FYERS_SECRET_KEY", "FYERS_PIN", "FYERS_ENV_FILE", "HUB_DB_PATH", "FYERS_TOKEN_PATH"):
        monkeypatch.delenv(k, raising=False)
