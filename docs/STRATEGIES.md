# Strategies (20 kul: 14 numbered + S03b + 5 Greeks)

| Number | Naam | Source | File | Live order? | Test |
|---|---|---|---|---|---|
| STR01 | obi_delta | quantlab | `external/gts_quant_lab/gts_quant_lab/quantlab/strategies/s01_obi_delta.py` | nahi | quantlab tests (9 pass) |
| STR02 | stat_arb | quantlab | `external/gts_quant_lab/gts_quant_lab/quantlab/strategies/s02_stat_arb.py` | nahi | quantlab tests (9 pass) |
| STR03 | latency_arb | quantlab | `external/gts_quant_lab/gts_quant_lab/quantlab/strategies/s03_latency_arb.py` | nahi | quantlab tests (9 pass) |
| STR04 | microstructure | quantlab | `external/gts_quant_lab/gts_quant_lab/quantlab/strategies/s04_microstructure.py` | nahi | quantlab tests (9 pass) |
| STR05 | spoof_ml | quantlab | `external/gts_quant_lab/gts_quant_lab/quantlab/strategies/s05_spoof_ml.py` | nahi | quantlab tests (9 pass) |
| STR06 | volume_profile | quantlab | `external/gts_quant_lab/gts_quant_lab/quantlab/strategies/s06_volume_profile.py` | nahi | quantlab tests (9 pass) |
| STR07 | reversal_ai | quantlab | `external/gts_quant_lab/gts_quant_lab/quantlab/strategies/s07_reversal_ai.py` | nahi | quantlab tests (9 pass) |
| STR08 | fvg | quantlab | `external/gts_quant_lab/gts_quant_lab/quantlab/strategies/s08_fvg.py` | nahi | quantlab tests (9 pass) |
| STR09 | iceberg | quantlab | `external/gts_quant_lab/gts_quant_lab/quantlab/strategies/s09_iceberg.py` | nahi | quantlab tests (9 pass) |
| STR10 | session_ignition | quantlab | `external/gts_quant_lab/gts_quant_lab/quantlab/strategies/s10_session_ignition.py` | nahi | quantlab tests (9 pass) |
| STR11 | mean_reversion | quantstrat | `external/quant_stat_arb_framework/src/quantstrat/strategy.py` | nahi | quantstrat tests (6 pass) |
| STR12 | gamma_blast | bootstrap | `strategies/gamma_blast/strategy.py` | nahi | tests/unit/strategies/gamma_blast (option-chain CSV) |
| STR13 | three_pm_momentum | bootstrap | `strategies/three_pm_momentum/strategy.py` | nahi | tests/unit/strategies/three_pm_momentum |
| STR14 | sweep | sweep_strategy | `scripts/sweep_strategy.py` | HAAN (asli order) | registry proxy tested in tests/unit/strategies/sweep |
| S03b | liquidity_sweep | quantlab | `external/gts_quant_lab/gts_quant_lab/quantlab/strategies/s03_latency_arb.py` | nahi | tests/unit/strategies/test_registry_wiring.py |

## Greeks (G01-G05)

| Number | Naam | Source | File | Live order? | Test |
|---|---|---|---|---|---|
| G01 | gamma_vwap | Greeks | `all_strategies/greeks/gamma_vwap_strategy.py` | nahi | tests/unit/strategies/test_greeks_adapters.py |
| G02 | delta_vwap | Greeks | `all_strategies/greeks/delta_vwap_strategy.py` | nahi | tests/unit/strategies/test_greeks_adapters.py |
| G03 | vega_iv | Greeks | `all_strategies/greeks/vega_iv_strategy.py` | nahi | tests/unit/strategies/test_greeks_adapters.py |
| G04 | theta_straddle | Greeks | `all_strategies/greeks/theta_straddle_strategy.py` | nahi | registry block test (short legs unsupported) |
| G05 | greeks_confluence | Greeks | `all_strategies/greeks/greeks_confluence_strategy.py` | nahi | tests/unit/strategies/test_greeks_adapters.py |

Sample datasets are gitignored. Generate them with:

```bash
python -m cli.main make-sample                 # data/samples/sample_5m.csv
python -m cli.main make-options-sample         # data/samples/sample_options_5m.csv
```
