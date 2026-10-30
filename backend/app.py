"""Backend entry point. Abhi sirf /health + /audit (FastAPI ho to). Baaki routes service layer par banenge."""


def create_app():
    try:
        from fastapi import FastAPI
    except ImportError as e:
        raise RuntimeError("`pip install fastapi uvicorn` chahiye") from e
    from backend.api import audit, health
    app = FastAPI(title="strategy-validation-lab")
    app.include_router(health.router)
    app.include_router(audit.router)
    return app
