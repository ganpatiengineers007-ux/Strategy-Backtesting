from backend.middleware.authentication import is_authorized


def test_dev_mode_and_key():
    assert is_authorized({}, "") is True
    assert is_authorized({"x-api-key": "k"}, "k") is True
    assert is_authorized({"x-api-key": "bad"}, "k") is False and is_authorized({}, "k") is False
