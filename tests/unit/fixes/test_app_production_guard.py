"""Regression: production me API_KEY ke bina app start nahi hota."""
import os


def test_production_requires_api_key():
    try:
        import fastapi  # noqa: F401
    except ImportError:
        return  # fastapi is environment me nahi - ye test skip
    from backend.app import create_app

    keys = ("SVL_ENV", "API_KEY")
    saved = {k: os.environ.get(k) for k in keys}
    try:
        os.environ["SVL_ENV"] = "production"
        os.environ.pop("API_KEY", None)
        failed = False
        try:
            create_app()
        except RuntimeError:
            failed = True
        assert failed, "production me API_KEY bina start nahi hona chahiye"
        os.environ["API_KEY"] = "x" * 32
        assert create_app() is not None
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
