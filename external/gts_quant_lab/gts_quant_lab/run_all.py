"""Run all 10 strategies on synthetic data and write reports/summary.{csv,json}. Usage: python run_all.py"""
import csv, json, os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from quantlab.synth import make_book, make_two_venues, make_panel, make_session_bars
from quantlab.types import book_to_bars
from quantlab.backtest import run_backtest, run_panel_backtest
from quantlab.strategies import *

PPY_TICK, PPY_BAR = 252 * 23400, 252 * 1440


def main(out_dir="reports"):
    os.makedirs(out_dir, exist_ok=True)
    book, bars20, sess = make_book(), None, make_session_bars()
    bars20 = book_to_bars(book, 20)
    lead, lag = make_two_venues(book)
    px = make_panel()
    res = []
    jobs = [
        ("S01", lambda: run_backtest(book.mid, OBIDeltaStrategy().positions(book), 0.8, 1, PPY_TICK, OBIDeltaStrategy.name)),
        ("S02", lambda: run_panel_backtest(px, CrossSectionalStatArb().positions(px), 2.0, 1, 252, CrossSectionalStatArb.name)),
        ("S03a", lambda: run_backtest(lag, LatencyArbStrategy().positions((lead, lag)), 0.5, 1, PPY_TICK, LatencyArbStrategy.name)),
        ("S03b", lambda: run_backtest(sess.close, LiquiditySweepStrategy().positions(sess), 1.0, 1, PPY_BAR, LiquiditySweepStrategy.name)),
        ("S04", lambda: run_backtest(book.mid, MicrostructureStrategy().positions(book), 0.8, 1, PPY_TICK, MicrostructureStrategy.name)),
        ("S05", lambda: run_backtest(book.mid, SpoofMLStrategy().positions(book), 0.8, 1, PPY_TICK, SpoofMLStrategy.name)),
        ("S06", lambda: run_backtest(book.mid, VolumeProfileStrategy().positions(book), 0.8, 1, PPY_TICK, VolumeProfileStrategy.name)),
        ("S07", lambda: run_backtest(bars20.close, ReversalAIStrategy().positions(bars20), 1.0, 1, 252 * 1170, ReversalAIStrategy.name)),
        ("S08", lambda: run_backtest(sess.close, FVGStrategy().positions(sess), 1.0, 1, PPY_BAR, FVGStrategy.name)),
        ("S09", lambda: run_backtest(book.mid, IcebergStrategy().positions(book), 0.8, 1, PPY_TICK, IcebergStrategy.name)),
        ("S10", lambda: run_backtest(sess.close, SessionIgnitionStrategy().positions(sess), 1.0, 1, PPY_BAR, SessionIgnitionStrategy.name)),
    ]
    for key, fn in jobs:
        t = time.time(); r = fn(); s = r.summary(); s["id"] = key; s["secs"] = round(time.time() - t, 1); res.append(s)
        print(f"{key:5} {s['name'][:42]:42} sharpe={s['sharpe']:>7} ret%={s['total_return_%']:>7} dd%={s['max_dd_%']:>6} trades={s['trades']:>5} ({s['secs']}s)")
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(res, f, indent=2)
    with open(os.path.join(out_dir, "summary.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(res[0].keys())); w.writeheader(); w.writerows(res)
    return res


if __name__ == "__main__":
    main()
