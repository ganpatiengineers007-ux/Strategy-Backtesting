"""Strategy #2: Delta + VWAP trend.   python3 delta_vwap_strategy.py [data.csv]"""
import math
import gamma_vwap_strategy as G

TG_ATR = 3.0; Z_TH = 1.0; Z_N = 50; VOL_N = 20; VOL_MULT = 1.2


def signal(rows, i, vw):
    """z-score (delta का proxy) + VWAP के ऊपर/नीचे + volume की पुष्टि"""
    if i < Z_N:
        return 0
    cl = [r['c'] for r in rows[i - Z_N + 1:i + 1]]
    m = sum(cl) / Z_N
    sd = math.sqrt(sum((x - m) ** 2 for x in cl) / Z_N)
    av = G.avg_vol(rows, i, VOL_N)
    if sd == 0 or av is None or rows[i]['v'] < VOL_MULT * av:
        return 0
    z = (cl[-1] - m) / sd
    if z > Z_TH and cl[-1] > vw: return 1
    if z < -Z_TH and cl[-1] < vw: return -1
    return 0


if __name__ == '__main__':
    G.run("Strategy #2: Delta + VWAP trend", signal, tg_atr=TG_ATR)
