import csv

FIELDS = ["entry_ts", "exit_ts", "entry_price", "exit_price", "qty", "pnl", "fees", "reason"]


def write_trades(trades, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(trades)
    return str(path)
