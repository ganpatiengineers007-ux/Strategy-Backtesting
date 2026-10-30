"""Signal model (contracts/signal.schema.json). v0: long-only (BUY / EXIT)."""
from dataclasses import dataclass, asdict

VALID_SIDES = ("BUY", "EXIT")


@dataclass
class Signal:
    side: str
    stop_loss: float = None
    target: float = None
    size_hint: float = None
    reason: str = ""

    def to_dict(self):
        return asdict(self)

    def validate(self):
        if self.side not in VALID_SIDES:
            raise ValueError(f"UNSUPPORTED_SIDE:{self.side}")
        for name in ("stop_loss", "target"):
            v = getattr(self, name)
            if v is not None and v <= 0:
                raise ValueError(f"INVALID_{name.upper()}")
        if self.stop_loss and self.target and self.stop_loss >= self.target:
            raise ValueError("STOP_NOT_BELOW_TARGET")
