"""Strategy #4: Theta short-straddle (expiry के करीब, शांत बाज़ार में)

ATM straddle का भाव Black-Scholes से निकलता है (IV = realized vol का proxy, असली option chain नहीं)।
python3 theta_straddle_strategy.py [data.csv]
"""
import math, sys
import gamma_vwap_strategy as G

R = 0.07; DTE_MAX = 3.0; VOL_LOW = 0.8; VOL_SPIKE = 2.0; NEAR_VWAP = 0.001
RANGE_PCT = 0.005; RANGE_N = 20; VOL_N = 20; SL_MULT = 1.5; TP_MULT = 0.6
LAST_ENTRY = (14, 30); LEG_SLIP = 2 * G.SLIP; UNIT = 0.25   # UNIT = premium का हिस्सा; SL=SL_MULT*UNIT*P0, TP=TP_MULT*UNIT*P0
IV_FLOOR = 8.0; IV_MULT = 1.1


def ncdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def straddle(S, K, T, iv):
    """ATM call+put का Black-Scholes भाव (iv % में)"""
    s = iv / 100.0
    T = max(T, 1e-5)
    d1 = (math.log(S / K) + (R + s * s / 2) * T) / (s * math.sqrt(T))
    d2 = d1 - s * math.sqrt(T)
    call = S * ncdf(d1) - K * math.exp(-R * T) * ncdf(d2)
    put = K * math.exp(-R * T) * ncdf(-d2) - S * ncdf(-d1)
    return call + put


def realized_iv(rows, i, n=VOL_N):
    r = [math.log(rows[j]['c'] / rows[j - 1]['c']) for j in range(i - n + 1, i + 1)]
    m = sum(r) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in r) / (n - 1))
    return max(IV_FLOOR, sd * math.sqrt(75 * 252) * 100 * IV_MULT)


def dte_days(t):
    return (3 - t.weekday()) % 7          # अगला गुरुवार expiry माना है


def t_years(t, dte):
    mo = t.hour * 60 + t.minute
    return (dte + max((930 - mo) / 375.0, 0.0)) / 365.0


def backtest(rows):
    eq = G.CAPITAL; peak = eq; mdd = 0.0; trades = []; pos = None
    day = None; cpv = cv = 0.0; n_today = 0

    def close(prem, i, why):
        nonlocal eq, peak, mdd, pos
        pnl = (pos['p0'] - prem) * pos['q'] - 4 * LEG_SLIP * pos['q'] \
              - G.COST_BPS / 1e4 * (pos['p0'] + prem) * 2 * pos['q']
        eq += pnl; peak = max(peak, eq); mdd = max(mdd, (peak - eq) / peak)
        trades.append({'pnl': pnl, 'bars': i - pos['i'], 'why': why}); pos = None

    for i, b in enumerate(rows):
        if b['t'].date() != day:
            if pos:
                close(pos['last'], i, 'DATA_GAP')
            day = b['t'].date(); cpv = cv = 0.0; n_today = 0
        cpv += (b['h'] + b['l'] + b['c']) / 3 * b['v']; cv += b['v']
        vw = cpv / cv if cv else b['c']
        hm = (b['t'].hour, b['t'].minute)
        dte = dte_days(b['t'])

        if pos:
            prem = straddle(b['c'], pos['K'], t_years(b['t'], dte), pos['iv'])
            pos['last'] = prem
            av = G.avg_vol(rows, i, VOL_N)
            if hm >= G.EXIT_AT:
                close(prem, i, 'EOD')
            elif prem - pos['p0'] >= SL_MULT * UNIT * pos['p0']:
                close(prem, i, 'STOP')
            elif pos['p0'] - prem >= TP_MULT * UNIT * pos['p0']:
                close(prem, i, 'TARGET')
            elif av and b['v'] >= VOL_SPIKE * av:
                close(prem, i, 'VOLSPIKE')
            continue

        if n_today >= G.MAX_TRADES_DAY or not (G.ENTRY_FROM <= hm < LAST_ENTRY) or dte > DTE_MAX:
            continue
        if i < max(RANGE_N, VOL_N) + 1:
            continue
        w = rows[i - RANGE_N + 1:i + 1]
        rng = (max(r['h'] for r in w) - min(r['l'] for r in w)) / b['c']
        av = G.avg_vol(rows, i, VOL_N)
        if rng > RANGE_PCT or not av or b['v'] > VOL_LOW * av:
            continue
        if abs(b['c'] - vw) / vw > NEAR_VWAP:
            continue
        iv = realized_iv(rows, i)
        K = round(b['c'] / 50) * 50.0
        p0 = straddle(b['c'], K, t_years(b['t'], dte), iv)
        dist = SL_MULT * UNIT * p0
        q = eq * G.RISK / dist
        pos = {'K': K, 'iv': iv, 'p0': p0, 'q': q, 'i': i, 'last': p0}
        n_today += 1
    if pos:
        close(pos['last'], len(rows) - 1, 'EOD')
    return trades, mdd, eq


if __name__ == '__main__':
    rows, synth = G.load_data()
    t, mdd, eq = backtest(rows)
    G.report("Strategy #4: Theta short-straddle", t, mdd, eq, synth,
             note="NOTE: भाव Black-Scholes मॉडल से (iv = realized-vol proxy). असली option chain/IV बाद में।")
