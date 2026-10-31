"""Parameter sensitivity: har float parameter +-20%. Neighbourhood me edge bana rehna chahiye."""
from backtest.engine import run_backtest
from metrics import expectancy

MIN_TRADES = 5
FACTORS = (0.8, 1.2)


def variants(params):
    return [{**params, k: round(v * f, 6)} for k, v in params.items()
            if isinstance(v, float) and v > 0 for f in FACTORS]


def decide(base_exp, var_exps):
    if base_exp <= 0:
        return "UNAVAILABLE", "BASE_NOT_PROFITABLE"
    if not var_exps:
        return "UNAVAILABLE", "NO_FLOAT_PARAMS"
    share = sum(1 for e in var_exps if e > 0) / len(var_exps)
    return ("PASS" if share >= 0.75 else "FAIL"), ""


def run(dataset, factory, config=None):
    base = factory()
    res = run_backtest(dataset, base, config)
    if len(res.trades) < MIN_TRADES:
        return {"status": "UNAVAILABLE", "reason": "TOO_FEW_TRADES"}
    exps = [expectancy.expectancy(run_backtest(dataset, type(base)(p), config).trades) for p in variants(base.params)]
    status, reason = decide(expectancy.expectancy(res.trades), exps)
    return {"status": status, "reason": reason, "variant_expectancies": exps}
