from backend.services.report_service import get_report


def compare(run_ids, root="runs"):
    if not isinstance(run_ids, list) or not 2 <= len(run_ids) <= 10:
        raise ValueError("2 se 10 run_ids chahiye")
    rows = []
    for rid in run_ids:
        r = get_report(rid, root)
        rows.append({"run_id": rid, "status": r["status"], "validation": r["validation"].get("status"), "metrics": r["metrics"]})
    return {"runs": rows, "metric_names": sorted({k for r in rows for k in r["metrics"]})}
