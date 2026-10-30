from __future__ import annotations
from abc import ABC, abstractmethod
import numpy as np


class Strategy(ABC):
    """positions() -> target exposure per row in [-1, 1] (or a (T, N) weight matrix). Decision at row t
    may only use data up to and including row t; the backtester adds the execution lag."""
    name = "strategy"

    @abstractmethod
    def positions(self, data) -> np.ndarray: ...
