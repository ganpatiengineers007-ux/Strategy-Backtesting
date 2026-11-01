"""Strategy #3: Vega IV-expansion breakout.   python3 vega_iv_strategy.py [data.csv]"""
import math
import gamma_vwap_strategy as G

TG_ATR = 2.5; Z_TH = 1.0; Z_N = 50; VOL_N = 20; VOL_MULT = 1.5; BRK_N = 20


def signal(rows, i, vw):
    """volatility-expansion (IV proxy: ATR(5)/ATR(Z_N)>1) + BRK_N bars का breakout + volume"""
    if i < max(Z_N, BRK_N) + 1:
        return 0
    a_s = G.atr_at(rows, i, 5); a_l = G.atr_at(rows, i, Z_N)
    av = G.avg_vol(rows, i, VOL_N)
    if not a_s or not a_l or av is None:
        return 0
    b = rows[i]
    if a_s / a_l <= 1.0 or b['v'] < VOL_MULT * av:
        return 0
    hi = max(r['h'] for r in rows[i - BRK_N:i]); lo = min(r['l'] for r in rows[i - BRK_N:i])
    cl = [r['c'] for r in rows[i - Z_N + 1:i + 1]]
    m = sum(cl) / Z_N; sd = math.sqrt(sum((x - m) ** 2 for x in cl) / Z_N)
    z = (b['c'] - m) / sd if sd else 0
    if b['c'] > hi and z > Z_TH: return 1
    if b['c'] < lo and z < -Z_TH: return -1
    return 0


if __name__ == '__main__':
    G.run("Strategy #3: Vega IV-expansion breakout", signal, tg_atr=TG_ATR)
