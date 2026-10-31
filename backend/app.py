"""Backend entry point (FastAPI). Chalane ke liye: pip install fastapi uvicorn; uvicorn --factory backend.app:create_app
Env: API_KEY (set ho to X-API-Key zaroori, /health chhodkar), RUNS_ROOT, DATA_DIR, DATABASE_URL."""
import os


def create_app():
    try:
        from fastapi import FastAPI, Request
        from fastapi.responses import JSONResponse
    except ImportError as e:
        raise RuntimeError("`pip install fastapi uvicorn` chahiye") from e
    from backend.api import audit, backtests, comparisons, datasets, health, reports, strategies, validation
    from backend.middleware.authentication import is_authorized
    from backend.middleware.request_id import new_request_id

    app = FastAPI(title="strategy-validation-lab")

    @app.middleware("http")
    async def guard(request: Request, call_next):
        rid = new_request_id()
        if request.url.path != "/health" and not is_authorized(request.headers, os.environ.get("API_KEY", "")):
            return JSONResponse({"error": "unauthorized", "request_id": rid}, status_code=401)
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response

    for module in (health, strategies, datasets, backtests, validation, comparisons, reports, audit):
        app.include_router(module.router)
    return app
