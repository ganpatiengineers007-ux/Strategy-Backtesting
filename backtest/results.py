from dataclasses import dataclass, field, asdict


@dataclass
class BacktestResult:
    status: str                       # COMPLETED | BLOCKED | HALTED
    reason: str = ""
    trades: list = field(default_factory=list)
    equity: list = field(default_factory=list)
    rejections: list = field(default_factory=list)
    config: dict = field(default_factory=dict)
    meta: dict = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)
