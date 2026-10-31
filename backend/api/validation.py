from backend.api import backtests
from backend.api.common import guarded, make_router, runs_root
from backend.services import validation_service


def start(payload: dict):
    """POST /validations: pura pipeline chalta hai; payload me optional validation={'split':..,'windows':..}."""
    return backtests.start(payload)


def get_one(run_id: str):
    return validation_service.get_validation(run_id, runs_root())


router = make_router()
if router is not None:
    router.post("/validations")(guarded(start))
    router.get("/validations/{run_id}")(guarded(get_one))
