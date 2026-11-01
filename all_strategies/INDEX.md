# Strategy-Backtesting: Strategy INDEX (1 Nov 2026)

कुल अलग strategies: **19** (14 क्रमांकित global + 5 Greeks). कुछ भी हटाया नहीं गया है।

## A. क्रमांकित global strategies (STR01 से STR14)

| # | नाम | विचार (एक पंक्ति) | by_number | strategies/ (plug-in) | quantlab |
|---|---|---|---|---|---|
| 01 | obi_delta | US: order-book imbalance / delta | हाँ | हाँ | s01 |
| 02 | stat_arb | चीन: statistical arbitrage | हाँ | हाँ | s02 |
| 03 | latency_arb | सिंगापुर: latency arbitrage | हाँ | हाँ | s03 |
| 04 | microstructure | रूस: microstructure absorption | हाँ | हाँ | s04 |
| 05 | spoof_ml | जापान: ML spoofing detection | हाँ | हाँ | s05 |
| 06 | volume_profile | ऑस्ट्रेलिया: volume profile / POC | हाँ | हाँ | s06 |
| 07 | reversal_ai | multi-feature reversal AI | हाँ | हाँ | s07 |
| 08 | fvg | Fair Value Gap | हाँ | हाँ | s08 |
| 09 | iceberg | iceberg order detection | हाँ | हाँ | s09 |
| 10 | session_ignition | session ignition | हाँ | हाँ | s10 |
| 11 | mean_reversion | mean reversion | हाँ | हाँ | - |
| 12 | gamma_blast | gamma blast | हाँ | हाँ (gamma_blast/) | - |
| 13 | three_pm_momentum | 3 PM momentum | हाँ | हाँ (three_pm_momentum/) | - |
| 14 | sweep | liquidity sweep | हाँ | हाँ (sweep/) | - |

अतिरिक्त: `all_strategies/sweep/sweep_strategy.py`, `all_strategies/quantstrat/strategy.py`

## B. Greeks strategies (G01 से G05)

| # | नाम | फ़ाइल | विचार |
|---|---|---|---|
| G01 | Gamma + VWAP + Volume | gamma_vwap_strategy.py (core engine भी) | max-gamma strike के पास + volume spike, direction VWAP से |
| G02 | Delta + VWAP trend | delta_vwap_strategy.py | z-score + VWAP + volume |
| G03 | Vega IV-expansion breakout | vega_iv_strategy.py | ATR(5)/ATR(50) > 1 + 20-bar breakout + volume |
| G04 | Theta short-straddle | theta_straddle_strategy.py | expiry के पास, शांत range में ATM straddle बेचना (Black-Scholes) |
| G05 | Multi-Greek confluence | greeks_confluence_strategy.py | G01, G02, G03 में से 2+ की सहमति |

जगह: कोड `all_strategies/greeks/`, plug-in adapters `strategies/G0x_*/strategy.py`

## C. सहायक फ़ाइलें (strategies नहीं)
strategies/base.py, context.py, models.py, validation.py, examples/example_strategy.py, all_strategies/quantlab/base.py, gts_lab/gts_quant_lab.py

## D. स्थिति
- सब strategies का synthetic डेटा पर ही परीक्षण हुआ है (Greeks 5: सब FAIL, जो random डेटा पर स्वाभाविक है)। असली डेटा पर परीक्षण बाकी।
- STR01 से STR11 और gamma_blast, three_pm_momentum, sweep: plug-in adapters repo में हैं।
- G01, G02, G03, G05: plug-in adapters बने हैं (long-only, synthetic bars पर signal निकलते हैं)।
- G04 theta: सिर्फ़ ढाँचा, क्योंकि Signal v0 में short और options legs नहीं हैं।
- STR01 से STR11 के adapters का `on_bar` अभी `return None` है, यानी असली लॉजिक जोड़ना बाकी।
