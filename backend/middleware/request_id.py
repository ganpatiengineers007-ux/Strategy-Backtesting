import uuid


def new_request_id():
    return uuid.uuid4().hex
