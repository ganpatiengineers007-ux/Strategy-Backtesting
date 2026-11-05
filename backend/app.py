"""Backend entry point (FastAPI). Chalane ke liye: pip install fastapi uvicorn; uvicorn --factory backend.app:create_app
Env: API_KEY (set ho to X-API-Key zaroori, /health chhodkar), RUNS_ROOT, DATA_DIR, DATABASE_URL."""
import os


def _is_production():
    return os.environ.get("SVL_ENV", "").strip().lower() in ("production", "prod")


def _enforce_production_settings():
    """Production me API_KEY khaali ho to app start hi na ho (khula API nahi chalega)."""
    import logging

    key = os.environ.get("API_KEY", "").strip()
    if _is_production() and not key:
        raise RuntimeError("SVL_ENV=production hai par API_KEY khaali hai - API_KEY set karo")
    if _is_production() and len(key) < 32:
        raise RuntimeError("SVL_ENV=production me API_KEY kam se kam 32 characters ka hona chahiye")
    if _is_production() and os.environ.get("RUN_ISOLATED") != "1":
        logging.getLogger("backend").warning("RUN_ISOLATED=1 nahi hai - strategy code API process me chalega")


def _run_migrations():
    url = os.environ.get("DATABASE_URL", "")
    if url.startswith("sqlite:///"):
        from scripts.migrate import migrate

        migrate(url[len("sqlite:///"):])


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
    import logging
    import time

    from backend.api import audit, auth, backtests, brokers, comparisons, datasets, health, hub, reports, strategies, validation
    from backend.auth.session import is_authorized
    from backend.middleware.rate_limit import SlidingWindowLimiter
    from backend.middleware.request_id import new_request_id
    from observability import metrics
    from observability.logging import setup_logging

    _enforce_production_settings()
    _run_migrations()
    setup_logging(os.environ.get("LOG_LEVEL", "INFO"), os.environ.get("LOG_JSON", "1") == "1")
    log = logging.getLogger("backend.request")
    limiter = SlidingWindowLimiter(int(os.environ.get("RATE_LIMIT_PER_MINUTE", "120") or "0"), 60)
    app = FastAPI(title="strategy-validation-lab")
    _add_cors(app)

    def _client_key(request):
        real = request.headers.get("x-real-ip")
        forwarded = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        return real or forwarded or (request.client.host if request.client else "unknown")

    @app.middleware("http")
    async def guard(request: Request, call_next):
        rid = new_request_id()
        started = time.perf_counter()
        path = request.url.path
        # Auth endpoints are public (login/me/logout); health is public
        is_public = path == "/health" or path.startswith("/auth/")
        if request.method == "OPTIONS" or is_public:
            response = await call_next(request)
        elif not limiter.allow(_client_key(request)):
            metrics.inc("rate_limited")
            response = JSONResponse({"error": "rate_limited", "request_id": rid}, status_code=429,
                                    headers={"Retry-After": str(limiter.retry_after(_client_key(request)))})
        elif not is_authorized(request.headers, os.environ.get("API_KEY", ""), request.cookies):
            response = JSONResponse({"error": "unauthorized", "request_id": rid}, status_code=401)
        else:
            response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        elapsed_ms = (time.perf_counter() - started) * 1000
        log.info("%s %s %s %.1fms", request.method, path, response.status_code, elapsed_ms)
        metrics.inc("requests_total")
        metrics.inc(f"status_{response.status_code}")
        return response

    for module in (health, auth, strategies, datasets, backtests, validation, comparisons, reports, audit, brokers, hub):
        app.include_router(module.router)
    return app
