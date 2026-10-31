from backend.api.common import guarded, make_router, runs_root
from backend.services import report_service


def get_one(run_id: str):
    return report_service.get_report(run_id, runs_root())


router = make_router()
if router is not None:
    router.get("/reports/{run_id}")(guarded(get_one))
