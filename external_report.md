# External files report

- gts_quant_lab.zip: extracted -> external/gts_quant_lab
- quant_stat_arb_framework.zip: extracted -> external/quant_stat_arb_framework

## external/gts_quant_lab/gts_quant_lab/quantlab/__init__.py  (2 lines, sha 01ba4719c80b)
- imports: -
- classes: -
- functions: -

## external/gts_quant_lab/gts_quant_lab/quantlab/backtest.py  (72 lines, sha ed10dd638579)
- imports: __future__, dataclasses, numpy
- MISSING libraries: numpy  (pip install ...)
- classes: Result(1 methods)
- functions: _metrics, run_backtest, run_panel_backtest

## external/gts_quant_lab/gts_quant_lab/quantlab/ml.py  (73 lines, sha f4877ede109a)
- imports: __future__, numpy
- MISSING libraries: numpy  (pip install ...)
- classes: MLP(5 methods)
- functions: walk_forward_probs

## external/gts_quant_lab/gts_quant_lab/quantlab/risk.py  (45 lines, sha bf8f7cffd23c)
- imports: __future__, numpy
- MISSING libraries: numpy  (pip install ...)
- classes: KillSwitch(4 methods)
- functions: vol_scale, kelly_fraction, apply_kill_switch

## external/gts_quant_lab/gts_quant_lab/quantlab/strategies/__init__.py  (12 lines, sha 89e4ed371343)
- imports: -
- classes: -
- functions: -

## external/gts_quant_lab/gts_quant_lab/quantlab/strategies/base.py  (13 lines, sha 879116f9bdc2)
- imports: __future__, abc, numpy
- MISSING libraries: numpy  (pip install ...)
- classes: Strategy(1 methods)
- functions: -
- STRATEGY CANDIDATE: Strategy bases=['ABC'] methods=[]

## external/gts_quant_lab/gts_quant_lab/quantlab/strategies/s01_obi_delta.py  (47 lines, sha addc7a3e1b27)
- imports: __future__, dataclasses, numpy
- MISSING libraries: numpy  (pip install ...)
- classes: OBIDeltaConfig(0 methods), OBIDeltaStrategy(3 methods)
- functions: -
- STRATEGY CANDIDATE: OBIDeltaStrategy bases=['Strategy'] methods=[]

## external/gts_quant_lab/gts_quant_lab/quantlab/strategies/s02_stat_arb.py  (85 lines, sha 43e5bb6345b2)
- imports: __future__, dataclasses, numpy, warnings
- MISSING libraries: numpy  (pip install ...)
- classes: StatArbConfig(0 methods), CrossSectionalStatArb(3 methods), KalmanPair(4 methods)
- functions: _cs_z
- STRATEGY CANDIDATE: CrossSectionalStatArb bases=['Strategy'] methods=[]

## external/gts_quant_lab/gts_quant_lab/quantlab/strategies/s03_latency_arb.py  (80 lines, sha aa851d3dfa12)
- imports: __future__, dataclasses, numpy
- MISSING libraries: numpy  (pip install ...)
- classes: LatencyArbConfig(0 methods), LatencyArbStrategy(2 methods), SweepConfig(0 methods), LiquiditySweepStrategy(2 methods)
- functions: estimate_lead_lag
- STRATEGY CANDIDATE: LatencyArbStrategy bases=['Strategy'] methods=[]
- STRATEGY CANDIDATE: LiquiditySweepStrategy bases=['Strategy'] methods=[]

## external/gts_quant_lab/gts_quant_lab/quantlab/strategies/s04_microstructure.py  (79 lines, sha 673b67689c36)
- imports: __future__, dataclasses, numpy
- MISSING libraries: numpy  (pip install ...)
- classes: MicroConfig(0 methods), MicrostructureStrategy(3 methods)
- functions: vpin, kyle_lambda
- STRATEGY CANDIDATE: MicrostructureStrategy bases=['Strategy'] methods=[]

## external/gts_quant_lab/gts_quant_lab/quantlab/strategies/s05_spoof_ml.py  (77 lines, sha 9e1e88520306)
- imports: __future__, dataclasses, numpy
- MISSING libraries: numpy  (pip install ...)
- classes: SpoofConfig(0 methods), SpoofMLStrategy(4 methods)
- functions: spoof_features
- STRATEGY CANDIDATE: SpoofMLStrategy bases=['Strategy'] methods=[]

## external/gts_quant_lab/gts_quant_lab/quantlab/strategies/s06_volume_profile.py  (98 lines, sha 242cfba7eb44)
- imports: __future__, dataclasses, numpy
- MISSING libraries: numpy  (pip install ...)
- classes: VPConfig(0 methods), VolumeProfileStrategy(2 methods)
- functions: build_profile
- STRATEGY CANDIDATE: VolumeProfileStrategy bases=['Strategy'] methods=[]

## external/gts_quant_lab/gts_quant_lab/quantlab/strategies/s07_reversal_ai.py  (89 lines, sha e2b9367b2c91)
- imports: __future__, dataclasses, numpy
- MISSING libraries: numpy  (pip install ...)
- classes: ReversalConfig(0 methods), ReversalAIStrategy(4 methods)
- functions: reversal_features
- STRATEGY CANDIDATE: ReversalAIStrategy bases=['Strategy'] methods=[]

## external/gts_quant_lab/gts_quant_lab/quantlab/strategies/s08_fvg.py  (64 lines, sha df6d58757612)
- imports: __future__, dataclasses, numpy
- MISSING libraries: numpy  (pip install ...)
- classes: FVGConfig(0 methods), FVGStrategy(2 methods)
- functions: -
- STRATEGY CANDIDATE: FVGStrategy bases=['Strategy'] methods=[]

## external/gts_quant_lab/gts_quant_lab/quantlab/strategies/s09_iceberg.py  (47 lines, sha 8f55d40e9626)
- imports: __future__, dataclasses, numpy
- MISSING libraries: numpy  (pip install ...)
- classes: IcebergConfig(0 methods), IcebergStrategy(4 methods)
- functions: -
- STRATEGY CANDIDATE: IcebergStrategy bases=['Strategy'] methods=[]

## external/gts_quant_lab/gts_quant_lab/quantlab/strategies/s10_session_ignition.py  (53 lines, sha 59ef1eca9b02)
- imports: __future__, dataclasses, numpy
- MISSING libraries: numpy  (pip install ...)
- classes: SessionConfig(0 methods), SessionIgnitionStrategy(2 methods)
- functions: -
- STRATEGY CANDIDATE: SessionIgnitionStrategy bases=['Strategy'] methods=[]

## external/gts_quant_lab/gts_quant_lab/quantlab/synth.py  (136 lines, sha fc2244ab6d73)
- imports: __future__, datetime, numpy
- MISSING libraries: numpy  (pip install ...)
- classes: -
- functions: make_book, make_two_venues, make_panel, make_session_bars

## external/gts_quant_lab/gts_quant_lab/quantlab/types.py  (70 lines, sha 971cd128952d)
- imports: __future__, dataclasses, numpy
- MISSING libraries: numpy  (pip install ...)
- classes: BookSeries(4 methods), Bars(1 methods)
- functions: book_to_bars

## external/gts_quant_lab/gts_quant_lab/quantlab/utils.py  (112 lines, sha c2be02cda0d2)
- imports: __future__, numpy
- MISSING libraries: numpy  (pip install ...)
- classes: -
- functions: ema, _pad, rsum, rmean, rstd, rmax, rmin, zscore, shift, rmean2, rstd2, to_position

## external/gts_quant_lab/gts_quant_lab/run_all.py  (45 lines, sha 4e01314b580e)
- imports: csv, json, numpy, os, quantlab, sys, time
- MISSING libraries: numpy, quantlab  (pip install ...)
- classes: -
- functions: main
- import par 1 top-level statements chalte hain (side-effect ka khatra)

## external/gts_quant_lab/gts_quant_lab/tests/test_all.py  (129 lines, sha a67153b1c4ba)
- imports: numpy, os, quantlab, sys
- MISSING libraries: numpy, quantlab  (pip install ...)
- classes: -
- functions: _cut, _cut_bars, _valid, test_tick_strategies_valid_and_causal, test_bar_strategies_valid_and_causal, test_ml_strategies, test_stat_arb_and_kalman, test_latency_arb_lead_lag, test_volume_profile_math, test_microstructure_helpers, test_backtest_engine_no_lookahead_and_costs, test_risk_and_mlp
- import par 1 top-level statements chalte hain (side-effect ka khatra)

## external/quant_stat_arb_framework/examples/run_backtest.py  (36 lines, sha b86145511909)
- imports: logging, numpy, pandas, quantstrat
- MISSING libraries: numpy, pandas, quantstrat  (pip install ...)
- classes: -
- functions: synthetic_bars
- import par 1 top-level statements chalte hain (side-effect ka khatra)

## external/quant_stat_arb_framework/src/quantstrat/__init__.py  (7 lines, sha 7b911fa1f67e)
- imports: -
- classes: -
- functions: -

## external/quant_stat_arb_framework/src/quantstrat/backtest.py  (77 lines, sha f12e4983bdae)
- imports: dataclasses, pandas
- MISSING libraries: pandas  (pip install ...)
- classes: BacktestResult(0 methods)
- functions: run_backtest

## external/quant_stat_arb_framework/src/quantstrat/config.py  (44 lines, sha 78bfb0a5c219)
- imports: dataclasses
- classes: StrategyConfig(1 methods), RiskConfig(1 methods)
- functions: -
- STRATEGY CANDIDATE: StrategyConfig bases=[] methods=[]

## external/quant_stat_arb_framework/src/quantstrat/data.py  (17 lines, sha 35d1580462b7)
- imports: logging, pandas
- MISSING libraries: pandas  (pip install ...)
- classes: -
- functions: load_csv

## external/quant_stat_arb_framework/src/quantstrat/execution.py  (29 lines, sha 83209df472ae)
- imports: dataclasses, logging
- classes: ExecutionResult(0 methods), DryRunExecutor(2 methods)
- functions: -

## external/quant_stat_arb_framework/src/quantstrat/indicators.py  (54 lines, sha 05b04fdd35eb)
- imports: numpy, pandas
- MISSING libraries: numpy, pandas  (pip install ...)
- classes: -
- functions: validate_ohlcv, rolling_zscore, true_range, atr, book_imbalance, oi_change_pct

## external/quant_stat_arb_framework/src/quantstrat/microstructure.py  (26 lines, sha 18a83a3d211d)
- imports: pandas
- MISSING libraries: pandas  (pip install ...)
- classes: -
- functions: microstructure_allows

## external/quant_stat_arb_framework/src/quantstrat/models.py  (38 lines, sha 43d34f7bc9f5)
- imports: dataclasses, enum, typing
- classes: Side(0 methods), Signal(0 methods), OrderIntent(0 methods), Position(0 methods)
- functions: -

## external/quant_stat_arb_framework/src/quantstrat/risk.py  (35 lines, sha 250262c8df1f)
- imports: math
- classes: RiskManager(2 methods)
- functions: -

## external/quant_stat_arb_framework/src/quantstrat/strategy.py  (66 lines, sha 4f05c73c061b)
- imports: logging, pandas
- MISSING libraries: pandas  (pip install ...)
- classes: MeanReversionStrategy(3 methods)
- functions: -
- STRATEGY CANDIDATE: MeanReversionStrategy bases=[] methods=['generate_signals']

## external/quant_stat_arb_framework/tests/test_indicators.py  (25 lines, sha 9085f65b9b37)
- imports: numpy, pandas, pytest, quantstrat
- MISSING libraries: numpy, pandas, quantstrat  (pip install ...)
- classes: -
- functions: sample, test_zscore_uses_full_window, test_atr_positive_after_warmup, test_validate_rejects_missing_column

## external/quant_stat_arb_framework/tests/test_risk_execution.py  (24 lines, sha 848bf33b5551)
- imports: pandas, pytest, quantstrat
- MISSING libraries: pandas, quantstrat  (pip install ...)
- classes: -
- functions: test_risk_sizing_and_dry_run, test_live_mode_is_blocked

## external/quant_stat_arb_framework/tests/test_strategy.py  (24 lines, sha 465bb7d6df4f)
- imports: numpy, pandas, quantstrat
- MISSING libraries: numpy, pandas, quantstrat  (pip install ...)
- classes: -
- functions: test_strategy_returns_valid_signal_objects

## backtest_lab-1.py  (377 lines, sha bdac4e0544a1)
- imports: matplotlib, numpy, os, pandas
- MISSING libraries: matplotlib, numpy, pandas  (pip install ...)
- classes: -
- functions: metrics, load_daily_csv, load_tick_csv, save_equity_chart, synthetic_pair, pairs_backtest, synthetic_universe, reversal_turnover_backtest, execution_sim, synthetic_ticks, detect_iceberg, merge_zones, iceberg_forward_test, market_making_sim, main
- import par 2 top-level statements chalte hain (side-effect ka khatra)

## backtest_lab.py  (377 lines, sha bdac4e0544a1)
- imports: matplotlib, numpy, os, pandas
- MISSING libraries: matplotlib, numpy, pandas  (pip install ...)
- classes: -
- functions: metrics, load_daily_csv, load_tick_csv, save_equity_chart, synthetic_pair, pairs_backtest, synthetic_universe, reversal_turnover_backtest, execution_sim, synthetic_ticks, detect_iceberg, merge_zones, iceberg_forward_test, market_making_sim, main
- import par 2 top-level statements chalte hain (side-effect ka khatra)

## sweep_strategy.py  (538 lines, sha bed469d06646)
- imports: collections, csv, datetime, dhanhq, logging, os, pandas, sys, threading, time, zoneinfo
- MISSING libraries: dhanhq, pandas  (pip install ...)
- classes: CandleBuilder(3 methods), DepthReader(3 methods), SweepStrategy(12 methods)
- functions: now_ist, fmt, compute_atr, classic_pivots, round_levels, journal_trade, parse_tick, depth_worker, main
- STRATEGY CANDIDATE: SweepStrategy bases=[] methods=[]
- NETWORK/BROKER libs: dhanhq
