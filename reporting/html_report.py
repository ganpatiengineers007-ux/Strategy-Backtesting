import html
from pathlib import Path
from string import Template

from reporting.charts import equity_svg

TEMPLATE = Path(__file__).parent / "templates" / "report.html"


def _rows(d):
    return "".join(f"<tr><td>{html.escape(str(k))}</td><td>{html.escape(str(v))}</td></tr>" for k, v in d.items())


def write(report, equity, path):
    checks = {k: f"{v.get('status')} {v.get('reason', '')}".strip()
              for k, v in report["validation"].get("checks", {}).items()}
    text = Template(TEMPLATE.read_text(encoding="utf-8")).safe_substitute(
        title=html.escape(report["run_id"]), status=html.escape(f"{report['status']} {report.get('reason', '')}"),
        validation=html.escape(str(report["validation"].get("status"))), metrics_rows=_rows(report["metrics"]),
        validation_rows=_rows(checks), chart=equity_svg(equity))
    Path(path).write_text(text, encoding="utf-8")
    return str(path)
