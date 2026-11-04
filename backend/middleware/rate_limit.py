"""Simple in-process sliding-window rate limiter (single-worker deployments)."""
import threading
import time
from collections import defaultdict, deque


class SlidingWindowLimiter:
    def __init__(self, limit=120, window_seconds=60.0):
        self.limit = max(0, int(limit))
        self.window = float(window_seconds)
        self._hits = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key, now=None):
        if self.limit <= 0:
            return True
        current = time.monotonic() if now is None else float(now)
        cutoff = current - self.window
        with self._lock:
            hits = self._hits[str(key)]
            while hits and hits[0] <= cutoff:
                hits.popleft()
            if len(hits) >= self.limit:
                return False
            hits.append(current)
            return True

    def retry_after(self, key, now=None):
        if self.limit <= 0:
            return 0
        current = time.monotonic() if now is None else float(now)
        with self._lock:
            hits = self._hits.get(str(key))
            if not hits:
                return 0
            return max(1, int(self.window - (current - hits[0])) + 1)

    def reset(self):
        with self._lock:
            self._hits.clear()
