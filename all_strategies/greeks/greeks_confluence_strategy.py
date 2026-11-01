"""Strategy #5: Multi-Greek confluence (Gamma + Delta + Vega की सहमति, Theta-regime फ़िल्टर)

ट्रेड तभी जब #1, #2, #3 में से कम से कम 2 signal एक ही दिशा में हों
और बाज़ार 'theta regime' (बहुत शांत/सिकुड़ी range) में न हो।
python3 greeks_confluence_strategy.py [data.csv]
"""
import gamma_vwap_strategy as G
import delta_vwap_strategy as D
import vega_iv_strategy as V

MIN_AGREE = 2; QUIET_RANGE_PCT = 0.003; RANGE_N = 20; TG_ATR = 2.5


def signal(rows, i, vw):
    if i < RANGE_N + 1:
        return 0
    w = rows[i - RANGE_N + 1:i + 1]
    if (max(r['h'] for r in w) - min(r['l'] for r in w)) / rows[i]['c'] < QUIET_RANGE_PCT:
        return 0                      # बहुत शांत: breakout/trend का मौक़ा नहीं
    score = G.signal(rows, i, vw) + D.signal(rows, i, vw) + V.signal(rows, i, vw)
    if score >= MIN_AGREE: return 1
    if score <= -MIN_AGREE: return -1
    return 0


if __name__ == '__main__':
    G.run("Strategy #5: Multi-Greek confluence", signal, tg_atr=TG_ATR)
