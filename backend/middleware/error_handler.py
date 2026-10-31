def to_error(exc):
    """Exception -> (http_status, body). Andar ki detail bahar nahi jaati."""
    if isinstance(exc, (KeyError, FileNotFoundError)):
        return 404, {"error": "not_found"}
    if isinstance(exc, ValueError):
        return 400, {"error": "bad_request", "detail": str(exc)}
    return 500, {"error": "internal_error"}
