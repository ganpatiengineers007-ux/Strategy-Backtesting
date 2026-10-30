"""/health route (FastAPI ho to router, warna plain function)."""


def health_payload():
    return {"status": "ok"}


try:
    from fastapi import APIRouter
    router = APIRouter()

    @router.get("/health")
    def health():
        return health_payload()
except ImportError:  # fastapi optional
    router = None
