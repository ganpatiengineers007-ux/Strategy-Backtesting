"""/audit route."""
from persistence import audit


def read_audit(root="runs", limit=100):
    return audit.read(root, limit)


try:
    from fastapi import APIRouter
    router = APIRouter()

    @router.get("/audit")
    def get_audit(limit: int = 100):
        return read_audit(limit=limit)
except ImportError:
    router = None
