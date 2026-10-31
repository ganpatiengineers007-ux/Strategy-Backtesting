"""Sliding-window rate limiter (per second + per minute). Thread-safe."""
from __future__ import annotations

import threading
import time
from collections import deque


class RateLimiter:
    def __init__(self, per_sec: int = 5, per_min: int = 50, clock=time.monotonic, sleep=time.sleep):
        self.per_sec, self.per_min = per_sec, per_min
        self._clock, self._sleep = clock, sleep
        self._sec: deque[float] = deque()
        self._min: deque[float] = deque()
        self._lock = threading.Lock()

    def acquire(self) -> None:
        while True:
            with self._lock:
                now = self._clock()
                while self._sec and now - self._sec[0] >= 1.0:
                    self._sec.popleft()
                while self._min and now - self._min[0] >= 60.0:
                    self._min.popleft()
                wait = 0.0
                if len(self._sec) >= self.per_sec:
                    wait = max(wait, 1.0 - (now - self._sec[0]))
                if len(self._min) >= self.per_min:
                    wait = max(wait, 60.0 - (now - self._min[0]))
                if wait <= 0:
                    self._sec.append(now)
                    self._min.append(now)
                    return
            self._sleep(wait + 0.01)
