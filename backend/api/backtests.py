"""/backtests. Default: job inline chalta hai. Env: BACKGROUND_WORKER=1 (thread), RUN_ISOLATED=1 (alag process + limits)."""
import os
from pathlib import Path

from backend.api.common import guarded, make_router, runs_root
from backend.dependencies import get_queue
from backend.jobs.worker import BackgroundWorker, run_next
from backend.schemas.backtest import BacktestRequest
from backend.services import dataset_service, report_service
from backend.services.backtest_service import run_full

_worker = None


def _handler(payload):
    req = BacktestRequest.from_dict(payload)
    data_path = str(Path(dataset_service.resolve(req.dataset)).resolve())
    out_root = str(Path(runs_root()).resolve())
    if os.environ.get("RUN_ISOLATED") == "1":
        from backend.jobs.isolated import run_isolated
        record = run_isolated({"strategy_id": req.strategy_id, "data_path": data_path, "params": req.params,
                               "config": req.config, "out_root": out_root, "symbol": req.symbol,
                               "timeframe": req.timeframe, "validation_opts": req.validation})["record"]
    else:
        record, _ = run_full(req.strategy_id, data_path, req.params, req.config, out_root=out_root, symbol=req.symbol,
                             timeframe=req.timeframe, validation_opts=req.validation)
    return {"run_id": record["run_id"], "status": record["status"], "validation_status": record["validation_status"],
            "reason": record["reason"]}


def _job_view(job):
    return {"job_id": job.job_id, "status": job.status.value, "result": job.result, "error": job.error}


def _ensure_worker():
    global _worker
    if _worker is None:
        _worker = BackgroundWorker(get_queue(), _handler)
    _worker.start()
    return _worker


def start(payload: dict):
    BacktestRequest.from_dict(payload)  # galat input turant ValueError
    q = get_queue()
    job = q.submit(payload)
    if os.environ.get("BACKGROUND_WORKER") == "1":
        _ensure_worker()
    else:
        run_next(q, _handler)
    return _job_view(job)


def list_runs():
    return report_service.list_runs(runs_root())


def get_one(item_id: str):
    if item_id.startswith("job-"):
        return _job_view(get_queue().get(item_id))
    return report_service.get_run(item_id, runs_root())


def get_results(item_id: str):
    r = report_service.get_report(item_id, runs_root())
    return {k: r.get(k) for k in ("run_id", "status", "reason", "metrics", "trades", "equity")}


router = make_router()
if router is not None:
    router.post("/backtests")(guarded(start))
    router.get("/backtests")(guarded(list_runs))
    router.get("/backtests/{item_id}")(guarded(get_one))
    router.get("/backtests/{item_id}/results")(guarded(get_results))
