"""GTS bridge: repo की plug-in registry (strategies.base / Context / Signal) और
Greeks backtest modules के बीच पुल।

Context से पिछली bars लेकर Greeks module वाले 'rows' बनाता है, signal पूछता है,
और उसे Signal(BUY/EXIT) में बदलता है। v0 सिर्फ़ long-only है, इसलिए short signal
(-1) को सिर्फ़ 'EXIT' (खुली position बंद) माना जाता है।
"""
from datetime import datetime

from strategies.models import Signal

HISTORY = 120   # इतनी पिछली bars से rows बनते हैं (Z_N=50 से ज़्यादा)

# bar के संभावित key-नाम (dict हो या object, दोनों चलेंगे)
_KEYS = {
    't': ('ts', 'timestamp', 't', 'time', 'datetime', 'date'),
    'o': ('open', 'o'), 'h': ('high', 'h'), 'l': ('low', 'l'),
    'c': ('close', 'c'), 'v': ('volume', 'v', 'vol'),
    'g': ('max_gamma_strike', 'gamma_strike', 'g'),
    'w': ('expiry_window', 'w'),
}


def _get(bar, names):
    for n in names:
        if isinstance(bar, dict):
            if n in bar and bar[n] not in (None, ''):
                return bar[n]
        elif getattr(bar, n, None) not in (None, ''):
            return getattr(bar, n)
    return None


def _time(x):
    if isinstance(x, datetime):
        return x
    if isinstance(x, (int, float)):          # epoch seconds (या ms)
        return datetime.fromtimestamp(x / 1000 if x > 1e11 else x)
    if isinstance(x, str):
        return datetime.fromisoformat(x.strip())
    return None


def norm(bar):
    """एक bar -> Greeks 'row' dict. ज़रूरी चीज़ें न मिलें तो None."""
    t = _time(_get(bar, _KEYS['t']))
    vals = [_get(bar, _KEYS[k]) for k in ('o', 'h', 'l', 'c', 'v')]
    if t is None or any(v is None for v in vals):
        return None
    g = _get(bar, _KEYS['g']); w = _get(bar, _KEYS['w'])
    return {'t': t, 'o': float(vals[0]), 'h': float(vals[1]), 'l': float(vals[2]),
            'c': float(vals[3]), 'v': float(vals[4]),
            'g': float(g) if g is not None else None,
            'w': int(w) if w is not None else 1}


def rows_from_ctx(ctx, n=HISTORY):
    bars = ctx._bars
    i = ctx.index
    rows = [norm(b) for b in bars[max(0, i - n + 1): i + 1]]
    return None if (not rows or any(r is None for r in rows)) else rows


def day_vwap(rows):
    """आख़िरी bar वाले दिन का VWAP"""
    day = rows[-1]['t'].date()
    pv = v = 0.0
    for r in rows:
        if r['t'].date() == day:
            pv += (r['h'] + r['l'] + r['c']) / 3 * r['v']; v += r['v']
    return pv / v if v else rows[-1]['c']


def decide(ctx, signal_fn, G, sl_atr=None, tg_atr=None, label=''):
    """Greeks signal_fn(rows, i, vwap) -> +1/-1/0 को Signal में बदलो।
    G = core module (gamma_vwap_strategy): EXIT_AT, ENTRY_FROM आदि वहीं से।"""
    rows = rows_from_ctx(ctx)
    if rows is None:
        return None
    i = len(rows) - 1
    b = rows[-1]
    hm = (b['t'].hour, b['t'].minute)
    in_pos = bool(ctx.position)

    if in_pos:                                    # खुली position: बंद करने की शर्तें
        if hm >= G.EXIT_AT:
            return Signal(side='EXIT', reason=f'{label}: EOD')
        if signal_fn(rows, i, day_vwap(rows)) == -1:
            return Signal(side='EXIT', reason=f'{label}: उल्टा signal')
        return None

    if not (G.ENTRY_FROM <= hm < G.NO_ENTRY_FROM):   # entry सिर्फ़ तय समय में
        return None
    if signal_fn(rows, i, day_vwap(rows)) != 1:      # long-only: सिर्फ़ +1
        return None
    atr = G.atr_at(rows, i)
    if not atr:
        return None
    sl = G.SL_ATR if sl_atr is None else sl_atr
    tg = G.TG_ATR if tg_atr is None else tg_atr
    sig = Signal(side='BUY', stop_loss=b['c'] - sl * atr, target=b['c'] + tg * atr,
                 reason=f'{label}: long')
    sig.validate()
    return sig
