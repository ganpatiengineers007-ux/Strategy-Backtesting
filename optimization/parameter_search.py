"""Grid search sirf pehle hisse (SEARCH) par; chuna hua param pichhle HOLDOUT par alag se parkha jaata hai.
Holdout PASS saboot nahi: jitne zyada trials, utna chance-luck. n_trials result me hai."""
import itertools

from backtest.engine import run_backtest
from metrics import expectancy
from optimization.constraints import satisfies
from optimization.experiment_tracking import log_trial

MIN_TRADES = 5


def grid(space):
    keys = list(space)
    return [dict(zip(keys, vals)) for vals in itertools.product(*(space[k] for k in keys))]


def search(dataset, make, space, config=None, is_ratio=0.6, min_trades=MIN_TRADES, rules=None,
           track_root=None, experiment_id="exp"):
    n = len(dataset.bars)
    k = int(n * is_ratio)
    search_ds, hold_ds = dataset.slice(0, k, "SEARCH"), dataset.slice(k, n, "HOLDOUT")
    trials = []
    for p in grid(space):
        if rules and not satisfies(p, rules):
            continue
        res = run_backtest(search_ds, make(p), config)
        t = {"params": p, "trades": len(res.trades), "expectancy": expectancy.expectancy(res.trades)}
        trials.append(t)
        if track_root:
            log_trial(track_root, experiment_id, p, {"trades": t["trades"], "expectancy": t["expectancy"], "phase": "search"})
    eligible = [t for t in trials if t["trades"] >= min_trades]
    if not eligible:
        return {"status": "UNAVAILABLE", "reason": "NO_ELIGIBLE_TRIALS", "n_trials": len(trials), "trials": trials}
    best = max(eligible, key=lambda t: t["expectancy"])
    hold = run_backtest(hold_ds, make(best["params"]), config)
    he = expectancy.expectancy(hold.trades)
    if track_root:
        log_trial(track_root, experiment_id, best["params"], {"trades": len(hold.trades), "expectancy": he, "phase": "holdout"})
    status = "UNAVAILABLE" if len(hold.trades) < min_trades else ("PASS" if he > 0 else "FAIL")
    return {"status": status, "best_params": best["params"], "in_sample_expectancy": best["expectancy"],
            "holdout_trades": len(hold.trades), "holdout_expectancy": he, "n_trials": len(trials), "trials": trials,
            "warning": "Holdout PASS != proof; n_trials ginti dekho"}
