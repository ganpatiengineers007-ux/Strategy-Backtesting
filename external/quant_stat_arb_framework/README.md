# Quant Statistical Arbitrage Framework

A research-first, modular Python framework for rolling Z-score mean reversion with
volume, order-book, and open-interest confirmation. It includes ATR-based exits,
risk-based sizing, a dry-run execution adapter, a historical bar simulator, logging,
and unit tests.

## Safety and scope

- `dry_run=True` is the default. The included executor only records simulated orders.
- No broker credentials, live broker adapter, or live order-routing implementation is included.
  Implement and independently validate a broker adapter before any live use.
- This is a single-instrument deviation/mean-reversion template, not a complete
  cointegration/pairs-trading engine. For genuine statistical arbitrage across assets,
  add a hedge-ratio/cointegration model and portfolio-level leg execution.
- A Z-score threshold is not proof of mean reversion. Trending regimes can keep prices
  statistically extended. Validate out-of-sample, include costs/slippage, and use
  walk-forward testing before considering deployment.
- Bar-based backtests execute at the next bar's open to avoid same-bar look-ahead.

## Install

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[test]"
pytest
```

## Expected input

OHLCV DataFrame indexed by timestamp with columns:
`open, high, low, close, volume`.

Optional microstructure columns:
- `bid_size`, `ask_size`: top-of-book displayed quantities
- `oi`: open interest
- `buy_volume`, `sell_volume`: aggressor-side volume estimates

If order-book fields are absent, the order-book filter is neutral only when
`require_orderbook=False`. OI is optional unless `require_oi=True`.

## Run the example

```bash
python examples/run_backtest.py
```

## Strategy flow

1. Compute rolling mean and sample standard deviation using data available through
   the current completed bar.
2. Compute `z = (close - rolling_mean) / rolling_std`.
3. Detect a threshold crossing: prior z at/above +threshold then current z below it
   for short; prior z at/below -threshold then current z above it for long. This
   is a re-entry/cross-back trigger intended to avoid blindly fading a still-accelerating
   move. Set `entry_mode="touch"` to trigger on threshold touch instead.
4. Require volume above its moving average times `volume_multiplier`.
5. Apply optional book-imbalance and OI-change confirmation.
6. Place simulated entry at next bar open; size from equity risk budget and ATR stop distance.
7. Manage stop-loss and take-profit using ATR multiples. If both stop and target are
   touched in the same bar, the conservative assumption is stop first.

## Configuration

See `StrategyConfig` and `RiskConfig` in `src/quantstrat/config.py`.
The strategy only emits signals; `RiskManager` creates an order intent and
`DryRunExecutor` simulates/records it.
