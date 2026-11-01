"""Strategy #1: Gamma + VWAP + Volume  (यही फ़ाइल सबका core engine भी है: import gamma_vwap_strategy as G)

चलाना:  python3 gamma_vwap_strategy.py [data.csv]
CSV columns: timestamp,open,high,low,close,volume  (वैकल्पिक: max_gamma_strike, expiry_window)
CSV न दो तो synthetic डेटा चलता है (नतीजों का कोई मतलब नहीं)।
"""
import csv, math, random, sys
from datetime import datetime, timedelta

CAPITAL = 1_000_000.0; RISK = 0.005; COST_BPS = 4.0; SLIP = 0.5
ATR_N = 14; SL_ATR = 1.5; TG_ATR = 2.5
VOL_MULT = 1.8; VOL_N = 20; GAMMA_BAND = 0.003; MAX_TRADES_DAY = 2
ENTRY_FROM = (9, 30); NO_ENTRY_FROM = (15, 0); EXIT_AT = (15, 15)
MIN_TRADES = 30


def load_csv(path):
    rows = []
    with open(path, newline='', encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            g = r.get('max_gamma_strike')
            w = r.get('expiry_window')
            rows.append({'t': datetime.fromisoformat(r['timestamp'].strip()),
                         'o': float(r['open']), 'h': float(r['high']),
                         'l': float(r['low']), 'c': float(r['close']),
                         'v': float(r['volume']),
                         'g': float(g) if g not in (None, '') else None,
                         'w': int(w) if w not in (None, '') else 1})
    rows.sort(key=lambda x: x['t'])
    return rows


def synthetic(days=120, seed=7):
    rnd = random.Random(seed); p = 22000.0; rows = []; d = datetime(2026, 1, 1, 9, 15)
    while len(rows) < days * 75:
        if d.weekday() < 5:
            for k in range(75):
                o = p; c = o + rnd.gauss(0, 12)
                rows.append({'t': d + timedelta(minutes=5 * k), 'o': o,
                             'h': max(o, c) + abs(rnd.gauss(0, 5)),
                             'l': min(o, c) - abs(rnd.gauss(0, 5)), 'c': c,
                             'v': rnd.randint(1000, 50000) * (3 if rnd.random() < .05 else 1),
                             'g': round(c / 100) * 100.0,
                             'w': 1 if d.weekday() in (2, 3) else 0})
                p = c
        d += timedelta(days=1)
    return rows


def atr_at(rows, i, n=ATR_N):
    if i < n:
        return None
    s = 0.0
    for j in range(i - n + 1, i + 1):
        pc = rows[j - 1]['c']
        s += max(rows[j]['h'] - rows[j]['l'], abs(rows[j]['h'] - pc), abs(rows[j]['l'] - pc))
    return s / n


def avg_vol(rows, i, n=VOL_N):
    if i < n:
        return None
    return sum(r['v'] for r in rows[i - n:i]) / n


def backtest(rows, signal, sl_atr=None, tg_atr=None, vol_mult=None):
    """signal(rows, i, vwap) -> +1 / -1 / 0. Entry अगली bar के open पर।"""
    sl_atr = SL_ATR if sl_atr is None else sl_atr
    tg_atr = TG_ATR if tg_atr is None else tg_atr
    eq = CAPITAL; peak = eq; mdd = 0.0
    trades = []; pos = None; pend = None
    day = None; cpv = 0.0; cv = 0.0; vw = None; n_today = 0

    def close_pos(px, b, why, i):
        nonlocal eq, peak, mdd, pos
        s = pos['side']; ex = px - s * SLIP
        pnl = s * (ex - pos['e']) * pos['q'] - COST_BPS / 1e4 * (pos['e'] + ex) * pos['q']
        eq += pnl; peak = max(peak, eq); mdd = max(mdd, (peak - eq) / peak)
        trades.append({'pnl': pnl, 'bars': i - pos['i'], 'why': why})
        pos = None

    for i, b in enumerate(rows):
        if b['t'].date() != day:
            if pos:
                close_pos(rows[i - 1]['c'], rows[i - 1], 'DATA_GAP', i)
            day = b['t'].date(); cpv = 0.0; cv = 0.0; n_today = 0; pend = None
        tp_ = (b['h'] + b['l'] + b['c']) / 3
        cpv += tp_ * b['v']; cv += b['v']
        vw = cpv / cv if cv else b['c']
        hm = (b['t'].hour, b['t'].minute)

        if pend and not pos:
            s, a = pend; pend = None
            e = b['o'] + s * SLIP; dist = sl_atr * a
            q = (eq * RISK) / dist if dist > 0 else 0
            if q > 0:
                pos = {'side': s, 'e': e, 'q': q, 'i': i,
                       'sl': e - s * dist, 'tp': e + s * tg_atr * a}
                n_today += 1

        if pos:
            s = pos['side']
            if hm >= EXIT_AT:
                close_pos(b['o'], b, 'EOD', i)
            elif (s == 1 and b['l'] <= pos['sl']) or (s == -1 and b['h'] >= pos['sl']):
                close_pos(pos['sl'], b, 'STOP', i)
            elif (s == 1 and b['h'] >= pos['tp']) or (s == -1 and b['l'] <= pos['tp']):
                close_pos(pos['tp'], b, 'TARGET', i)

        if (not pos and not pend and n_today < MAX_TRADES_DAY
                and ENTRY_FROM <= hm < NO_ENTRY_FROM):
            a = atr_at(rows, i)
            if a:
                s = signal(rows, i, vw)
                if s:
                    pend = (s, a)
    if pos:
        close_pos(rows[-1]['c'], rows[-1], 'EOD', len(rows) - 1)
    return trades, mdd, eq


def report(title, trades, mdd, eq, synth=False, note=None, min_trades=MIN_TRADES):
    n = len(trades)
    wins = [t['pnl'] for t in trades if t['pnl'] > 0]
    loss = [t['pnl'] for t in trades if t['pnl'] <= 0]
    gp = sum(wins); gl = -sum(loss)
    net = eq - CAPITAL
    pf = gp / gl if gl > 0 else float('inf')
    exp = net / n if n else 0.0
    why = {}
    for t in trades:
        why[t['why']] = why.get(t['why'], 0) + 1
    if synth:
        print("डेटा नहीं दिया -> synthetic (नतीजों का कोई मतलब नहीं)")
    print("=" * 52)
    print(title)
    print(f"Trades        : {n}")
    print(f"Net profit    : {net:,.0f}  ({net / CAPITAL * 100:.2f}%)")
    print(f"Win rate      : {len(wins) / n * 100 if n else 0:.1f}%")
    print(f"Profit factor : {pf:.2f}")
    print(f"Expectancy    : {exp:,.0f}")
    print(f"Max drawdown  : {mdd * 100:.2f}%")
    print(f"Avg hold bars : {sum(t['bars'] for t in trades) / n if n else 0:.1f}")
    for k in sorted(why):
        print(f"  exits {k:<7}: {why[k]}")
    ok = n >= min_trades and pf > 1.2 and exp > 0
    reasons = []
    if n < min_trades: reasons.append(f"ट्रेड < {min_trades}")
    if pf <= 1.2: reasons.append("PF <= 1.2")
    if exp <= 0: reasons.append("expectancy <= 0")
    print("Screen        : " + ("PASS" if ok else "FAIL (" + ", ".join(reasons) + ")"))
    print(note or "NOTE: underlying पर proxy P&L. option premium + असली Greeks बाद में।")
    print("=" * 52)


def load_data(argv=None):
    argv = sys.argv if argv is None else argv
    if len(argv) > 1:
        return load_csv(argv[1]), False
    return synthetic(), True


def run(title, signal, **kw):
    rows, synth = load_data()
    t, mdd, eq = backtest(rows, signal, **kw)
    report(title, t, mdd, eq, synth)


def signal(rows, i, vw):
    """Strategy #1: max-gamma strike के पास + volume spike + VWAP की तरफ़ direction"""
    b = rows[i]; av = avg_vol(rows, i)
    if av is None or b['g'] in (None, 0) or b['w'] != 1:
        return 0
    if abs(b['c'] - b['g']) / b['g'] > GAMMA_BAND or b['v'] < VOL_MULT * av:
        return 0
    return 1 if b['c'] > vw else -1


if __name__ == '__main__':
    run("Strategy #1: Gamma + VWAP + Volume", signal)
