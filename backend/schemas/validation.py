from dataclasses import dataclass, field


@dataclass
class ValidationRequest:
    strategy_id: str
    dataset_path: str
    params: dict = field(default_factory=dict)


@dataclass
class ValidationResponse:
    run_id: str
    status: str
    checks: dict = field(default_factory=dict)
