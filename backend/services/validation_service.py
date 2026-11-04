from backend.services.report_service import get_report


def get_validation(run_id, root="runs"):
    report = get_report(run_id, root)
    return {"run_id": run_id, **report["validation"], "reason": report.get("reason"),
            "dataset_id": report.get("dataset_id"), "synthetic": report.get("synthetic", False),
            "data_label": report.get("data_label", "real")}
