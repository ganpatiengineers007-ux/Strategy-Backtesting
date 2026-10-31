from backend.services.report_service import get_report


def get_validation(run_id, root="runs"):
    return {"run_id": run_id, **get_report(run_id, root)["validation"]}
