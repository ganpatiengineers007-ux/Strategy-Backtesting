"""जाँच: पाँचों Greeks adapters को synthetic bars पर चलाकर signals गिनता है।
repo root से चलाएँ:  python3 all_strategies/greeks/test_adapters.py
"""
import importlib.util, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "all_strategies" / "greeks"))
import gamma_vwap_strategy as G
from strategies.context import Context

rows = G.synthetic()
bars = [{'ts': r['t'].isoformat(), 'open': r['o'], 'high': r['h'], 'low': r['l'],
         'close': r['c'], 'volume': r['v'], 'max_gamma_strike': r['g'],
         'expiry_window': r['w']} for r in rows]

for d in sorted((ROOT / "strategies").glob("G0*_*")):
    spec = importlib.util.spec_from_file_location(d.name, d / "strategy.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    cls = [v for v in vars(m).values() if isinstance(v, type) and v.__name__.endswith("Adapter")][0]
    st = cls(); pos = None; buys = exits = 0
    for i in range(len(bars)):
        s = st.on_bar(Context(bars, i, pos))
        if s is None:
            continue
        s.validate()
        if s.side == "BUY": buys += 1; pos = True
        elif s.side == "EXIT": exits += 1; pos = None
    print(f"{d.name:28s} BUY={buys:4d} EXIT={exits:4d}")
