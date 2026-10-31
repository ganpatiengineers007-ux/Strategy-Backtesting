from backend.api.common import guarded, make_router, runs_root
from backend.dependencies import get_queue
from backend.jobs.worker import run_next
from backend.services import dataset_service, report_service
from backend.services.backtest_service import run_full


def _handler(p):
    record, _ = run_full(p["strategy_id"], dataset_service.resolve(p["dataset"]), p.get("params"), p.get("config"),
                         out_root=runs_root(), symbol=p.get("symbol", "UNKNOWN"), timeframe=p.get("timeframe", "UNKNOWN"))
    return {"run_id": record["run_id"], "status": record["status"], "validation_status": record["validation_status"],
            "reason": record["reason"]}


def _job_view(job):
    return {"job_id": job.job_id, "status": job.status.value, "result": job.result, "error": job.error}


def start(payload: dict):
    if not isinstance(payload, dict) or "strategy_id" not in payload or "dataset" not in payload:
        raise ValueError("strategy_id aur dataset chahiye")
    q = get_queue()
    job = q.submit(payload)
    run_next(q, _handler)  # abhi inline; background worker baad me
    return _job_view(job)


def list_runs():
    return report_service.list_runs(runs_root())


def get_one(item_id: str):
    if item_id.startswith("job-"):
        return _job_view(get_queue().get(item_id))
    return report_service.get_run(item_id, runs_root())


router = make_router()
if router is not None:
    router.post("/backtests")(guarded(start))
    router.get("/backtests")(guarded(list_runs))
    router.get("/backtests/{item_id}")(guarded(get_one))
