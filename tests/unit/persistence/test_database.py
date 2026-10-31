import pytest  # noqa: F401

from persistence.database import SqliteRunRepository


def test_save_get_list(tmp_path):
    repo = SqliteRunRepository(tmp_path / "t.db")
    rec = {"run_id": "r1", "strategy_id": "s", "status": "COMPLETED", "created_at": "2024-01-01T00:00:00"}
    repo.save("r1", rec)
    assert repo.get("r1") == rec and repo.list_ids() == ["r1"]
    try:
        repo.get("nope")
        raise AssertionError("KeyError expected")
    except KeyError:
        pass
