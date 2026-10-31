from optimization import experiment_tracking as et


def test_log_and_read(tmp_path):
    et.log_trial(tmp_path, "e1", {"a": 1}, {"trades": 3})
    et.log_trial(tmp_path, "e1", {"a": 2}, {"trades": 4})
    rows = et.read(tmp_path)
    assert [r["params"]["a"] for r in rows] == [1, 2] and rows[0]["experiment"] == "e1"
