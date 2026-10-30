from dataclasses import dataclass, field


@dataclass
class RunRecord:
    run_id: str
    strategy_id: str
    status: str
    data: dict = field(default_factory=dict)
