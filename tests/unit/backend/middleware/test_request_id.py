from backend.middleware.request_id import new_request_id


def test_unique_ids():
    assert new_request_id() != new_request_id() and len(new_request_id()) == 32
