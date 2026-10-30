import csv
import random
from datetime import date, timedelta
from pathlib import Path

from backend.services.backtest_service import run_full
from registry.registry import Registry


def make_sample_csv(path, days=120, seed=42):
    """Deterministic random-walk 5-min bars (sirf demo, asli data nahi)."""
    rng, price, d, rows = random.Random(seed), 1000.0, date(2024, 1, 1), []
    while len(rows) < days * 75:
        if d.weekday() < 5:
            for i in range(75):
                mins = 9 * 60 + 15 + i * 5
                o = price
                c = max(1.0, o * (1 + rng.gauss(0, 0.0008)))
                rows.append([f"{d.isoformat()}T{mins // 60:02d}:{mins % 60:02d}:00", round(o, 2),
                             round(max(o, c) * (1 + abs(rng.gauss(0, 0.0004))), 2),
                             round(min(o, c) * (1 - abs(rng.gauss(0, 0.0004))), 2), round(c, 2), rng.randint(100, 5000)])
                price = c
        d += timedelta(days=1)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ts", "open", "high", "low", "close", "volume"])
        w.writerows(rows)
    return str(path)


def cmd_list(_args):
    for sid in Registry().discover():
        print(sid)


def cmd_run(args):
    record, paths = run_full(args.strategy, args.data, out_root=args.out)
    print(f"status={record['status']} validation={record['validation_status']} reason={record['reason']}")
    print("report:", paths["html"])


def cmd_demo(args):
    csv_path = make_sample_csv(Path(args.out) / "sample_5m.csv")
    for sid in ("three_pm_momentum", "gamma_blast"):
        record, paths = run_full(sid, csv_path, out_root=args.out, symbol="DEMO", timeframe="5m")
        print(f"[{sid}] status={record['status']} validation={record['validation_status']} {record['reason']}")
        print("   report:", paths["html"])
