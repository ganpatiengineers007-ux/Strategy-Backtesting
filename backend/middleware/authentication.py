import hmac


def is_authorized(headers, expected_key):
    """expected_key khaali => dev mode (sab allowed). Warna X-API-Key match chahiye."""
    if not expected_key:
        return True
    return hmac.compare_digest(str(headers.get("x-api-key", "")), expected_key)
