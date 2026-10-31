from dataclasses import dataclass, field


@dataclass
class StrategySummary:
    id: str
    version: str
    required_data: list = field(default_factory=list)
    execution_modes: list = field(default_factory=list)
    live_trading_enabled: bool = False

    @classmethod
    def from_manifest(cls, m):
        lt = m.get("live_trading")
        return cls(str(m["id"]), str(m["version"]), list(m.get("required_data") or []),
                   list(m.get("execution_modes") or []), bool(lt.get("enabled")) if isinstance(lt, dict) else bool(lt))
