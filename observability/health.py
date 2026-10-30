import sys

from registry.registry import Registry


def check_health():
    try:
        n = len(Registry().discover())
        return {"status": "ok", "python": sys.version.split()[0], "strategies": n}
    except Exception as e:  # noqa: BLE001
        return {"status": "degraded", "error": f"{type(e).__name__}: {e}"}
