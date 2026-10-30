import time
from contextlib import contextmanager

SPANS = []


@contextmanager
def span(name):
    t = time.perf_counter()
    try:
        yield
    finally:
        SPANS.append({"name": name, "seconds": time.perf_counter() - t})
