import functools
import os


def runs_root():
    return os.environ.get("RUNS_ROOT", "runs")


def make_router():
    try:
        from fastapi import APIRouter
    except ImportError:
        return None
    return APIRouter()


def guarded(fn):
    """Handler errors -> HTTP errors (FastAPI ho to)."""
    try:
        from fastapi import HTTPException
    except ImportError:
        return fn
    from backend.middleware.error_handler import to_error

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except HTTPException:
            raise
        except Exception as e:  # noqa: BLE001
            status, body = to_error(e)
            raise HTTPException(status_code=status, detail=body) from e
    return wrapper
