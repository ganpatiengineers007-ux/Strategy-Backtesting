# ADR-0001: Language ownership
- Python: orchestration, backtest, validation, metrics, reporting (single owner).
- Go: validator service, sirf contracts ke zariye.
- C++: rolling stats, tab tak Python fallback jab tak benchmark gain na dikhaye.
- Rust: safe numeric module, same calculation ka dohra ownership nahi.
- Parity: `tests/contract/test_rolling_stats_parity.py` + har engine ka apna test.
