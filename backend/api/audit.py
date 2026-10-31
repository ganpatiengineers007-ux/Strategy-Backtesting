"""/audit route."""
from backend.api.common import guarded, make_router, runs_root
from persistence import audit


def read_audit(root=None, limit=100):
    return audit.read(root or runs_root(), limit)


def get_audit(limit: int = 100):
    return read_audit(limit=limit)


router = make_router()
if router is not None:
    router.get("/audit")(guarded(get_audit))
