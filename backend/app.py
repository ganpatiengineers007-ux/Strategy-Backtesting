"""Backend entry point (FastAPI). Chalane ke liye: pip install fastapi uvicorn; uvicorn --factory backend.app:create_app
Env: API_KEY (set ho to X-API-Key zaroori, /health chhodkar), RUNS_ROOT, DATA_DIR, DATABASE_URL."""
import os


def _is_production():
    return os.environ.get("SVL_ENV", "").strip().lower() in ("production", "prod")


def _enforce_production_settings():
    """Production me API_KEY khaali ho to app start hi na ho (khula API nahi chalega)."""
    import logging

    if _is_production() and not os.environ.get("API_KEY", "").strip():
        raise RuntimeError("SVL_ENV=production hai par API_KEY khaali hai - API_KEY set karo")
    if _is_production() and os.environ.get("RUN_ISOLATED") != "1":
        logging.getLogger("backend").warning("RUN_ISOLATED=1 nahi hai - strategy code API process me chalega")


def _cors_origins():
    return [o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()]


def _add_cors(app):
    origins = _cors_origins()
    if not origins:
        return
    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-API-Key"],
    )


def create_app():
    try:
        from fastapi import FastAPI, Request
        from fastapi.responses import JSONResponse
    except ImportError as e:
        raise RuntimeError("`pip install fastapi uvicorn` chahiye") from e
    from backend.api import audit, backtests, comparisons, datasets, health, hub, reports, strategies, validation
    from backend.middleware.authentication import is_authorized
    from backend.middleware.request_id import new_request_id

    _enforce_production_settings()
    app = FastAPI(title="strategy-validation-lab")
    _add_cors(app)

    @app.middleware("http")
    async def guard(request: Request, call_next):
        rid = new_request_id()
        if request.url.path != "/health" and not is_authorized(request.headers, os.environ.get("API_KEY", "")):
            return JSONResponse({"error": "unauthorized", "request_id": rid}, status_code=401)
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response

    for module in (health, strategies, datasets, backtests, validation, comparisons, reports, audit, hub):
        app.include_router(module.router)
    return app
