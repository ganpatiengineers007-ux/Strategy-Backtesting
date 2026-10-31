from backend.api.common import guarded, make_router, runs_root
from backend.services import validation_service


def get_one(run_id: str):
    return validation_service.get_validation(run_id, runs_root())


router = make_router()
if router is not None:
    router.get("/validations/{run_id}")(guarded(get_one))
