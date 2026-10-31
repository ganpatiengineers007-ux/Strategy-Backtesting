"""Validation order + overall status. Koi FAIL => FAIL; koi UNAVAILABLE => INCOMPLETE; tabhi PASS jab sab PASS."""
from backtest.engine import run_backtest
from validation import (cross_validation, leakage_checks, out_of_sample, overfitting, regime_analysis,
                        robustness, statistical_confidence, walk_forward)


def overall_status(checks):
    st = [c["status"] for c in checks.values()]
    if "FAIL" in st:
        return "FAIL"
    if "UNAVAILABLE" in st:
        return "INCOMPLETE"
    return "PASS"


def run_validation(dataset, factory, config=None, split=0.7, windows=4):
    base = run_backtest(dataset, factory(), config)
    if base.status == "BLOCKED":
        return {"status": "BLOCKED", "reason": base.reason, "checks": {}}
    oos = out_of_sample.run(dataset, factory, config, split)
    checks = {"leakage": leakage_checks.run(base, dataset), "out_of_sample": oos,
              "walk_forward": walk_forward.run(dataset, factory, config, windows),
              "cross_validation": cross_validation.run(dataset, factory, config), "overfitting": overfitting.run(oos),
              "robustness": robustness.run(dataset, factory, config), "regime_analysis": regime_analysis.run(dataset, base),
              "statistical_confidence": statistical_confidence.run(base)}
    return {"status": overall_status(checks), "checks": checks}
