from backend.middleware.error_handler import to_error


def test_mapping():
    assert to_error(KeyError("x"))[0] == 404 and to_error(ValueError("bad"))[0] == 400
    assert to_error(RuntimeError("secret"))[1] == {"error": "internal_error"}
