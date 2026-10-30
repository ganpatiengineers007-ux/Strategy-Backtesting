"""Strategy interface. Har strategy isi se guzregi; alag engine nahi banta."""
from abc import ABC, abstractmethod


class Strategy(ABC):
    strategy_id = "base"
    required_data = ()

    def __init__(self, params=None):
        self.params = dict(params or {})

    @abstractmethod
    def on_bar(self, ctx):
        """Return strategies.models.Signal ya None."""
