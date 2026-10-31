from backend.api.common import guarded, make_router, runs_root
from backend.services import comparison_service


def create(payload: dict):
    return comparison_service.compare(payload.get("run_ids") if isinstance(payload, dict) else None, runs_root())


router = make_router()
if router is not None:
    router.post("/comparisons")(guarded(create))
