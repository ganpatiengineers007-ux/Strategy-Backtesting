# GTS Quant Lab — 10 non-indicator quant strategies (pure numpy)

| ID | Strategy (origin style) | File | Input |
|----|-------------------------|------|-------|
| S01 | Order-book imbalance + cumulative-delta divergence (US) | s01_obi_delta.py | L2 book + trades |
| S02 | Cross-sectional stat-arb + Kalman pairs (China) | s02_stat_arb.py | price panel (T,N) |
| S03a | Cross-venue latency arbitrage (Singapore) | s03_latency_arb.py | two venue mids |
| S03b | Liquidity-sweep reversal (Singapore) | s03_latency_arb.py | bars |
| S04 | Microstructure absorption + VPIN + Kyle lambda (Russia) | s04_microstructure.py | L2 + trades |
| S05 | ML spoofing / layering detector (Japan) | s05_spoof_ml.py | L2 + labels |
| S06 | Volume profile POC/VAH/VAL (Australia) | s06_volume_profile.py | trades |
| S07 | Multi-feature neural reversal, 4-phase gate, walk-forward | s07_reversal_ai.py | bars |
| S08 | Fair Value Gap / institutional imbalance | s08_fvg.py | bars |
| S09 | Iceberg-order detection | s09_iceberg.py | L2 + trades |
| S10 | Session-open ignition (Tokyo/London/NY) | s10_session_ignition.py | 1-min bars (UTC) |

## Run
    pip install -r requirements.txt
    python tests/test_all.py     # 9 tests: validity, causality (no look-ahead), engine, risk, ML
    python run_all.py            # backtests on synthetic data -> reports/summary.csv|json

## Design rules
- `positions(data)` at row t uses data <= t only (tested by truncation invariance); the backtester adds 1-step execution lag and costs.
- ML: numpy MLP, expanding walk-forward with embargo = label horizon; S05 never trades in-sample.
- Risk: vol targeting, half-Kelly cap, latching drawdown kill-switch (`quantlab/risk.py`).

## IMPORTANT limits
- `quantlab/synth.py` PLANTS each effect so the pipelines can be verified. High Sharpe there only proves the code works,
  NOT that the edge exists in live markets. S07 is slightly negative on it (no planted reversal) - shown honestly.
- Real use: replace synth with real L2/L3 + trades, calibrate bins/thresholds, walk-forward + paper trade first.
- S03a needs co-located, sub-millisecond infrastructure; Python here is a research/signal reference, not an HFT engine.
- S05 needs labelled spoof episodes (from your own annotation/surveillance data).
