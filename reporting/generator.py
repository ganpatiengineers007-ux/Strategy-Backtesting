"""Reporting entry point: metrics + validation -> json/csv/html artifacts."""
from datetime import datetime, timezone
from pathlib import Path

from reporting import csv_export, html_report, json_report


def generate_report(run_id, result, metrics, validation, out_dir):
    out = Path(out_dir) / run_id
    out.mkdir(parents=True, exist_ok=True)
    report = {"run_id": run_id, "status": result.status, "reason": result.reason, "metrics": metrics,
              "validation": validation, "generated_at": datetime.now(timezone.utc).isoformat()}
    report["equity"] = result.equity[:: max(1, len(result.equity) // 500)]
    report["trades"] = result.trades[:1000]
    paths = {"json": json_report.write(report, out / "report.json"),
             "csv": csv_export.write_trades(result.trades, out / "trades.csv"),
             "html": html_report.write(report, result.equity, out / "report.html")}
    return report, paths
