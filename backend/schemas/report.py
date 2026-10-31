from dataclasses import dataclass


@dataclass
class ReportSummary:
    run_id: str
    status: str
    validation_status: str
    n_trades: int
    total_return_pct: float

    @classmethod
    def from_report(cls, r):
        m = r.get("metrics") or {}
        return cls(r["run_id"], r["status"], (r.get("validation") or {}).get("status", "UNKNOWN"),
                   int(m.get("n_trades", 0)), float(m.get("total_return_pct", 0.0)))
