import os
import time

from backend.api import backtests
from cli.commands import make_sample_csv


def test_background_job_completes(tmp_path):
    make_sample_csv(tmp_path / "data" / "s.csv", days=15)
    os.environ.update({"DATA_DIR": str(tmp_path / "data"), "RUNS_ROOT": str(tmp_path / "runs"), "BACKGROUND_WORKER": "1"})
    try:
        job = backtests.start({"strategy_id": "three_pm_momentum", "dataset": "s.csv"})
        deadline = time.time() + 90
        while time.time() < deadline:
            view = backtests.get_one(job["job_id"])
            if view["status"] in ("SUCCEEDED", "FAILED"):
                break
            time.sleep(0.2)
        assert view["status"] == "SUCCEEDED", view
        run_id = view["result"]["run_id"]
        res = backtests.get_results(run_id)
        assert res["run_id"] == run_id and "metrics" in res and len(res["equity"]) > 10
    finally:
        os.environ.pop("BACKGROUND_WORKER", None)
        if backtests._worker is not None:
            backtests._worker.stop()
