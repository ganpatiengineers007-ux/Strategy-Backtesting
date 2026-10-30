def vwap(bars):
    out, day, pv, vol = [], None, 0.0, 0.0
    for b in bars:
        if b.ts[:10] != day:
            day, pv, vol = b.ts[:10], 0.0, 0.0
        pv += (b.high + b.low + b.close) / 3.0 * b.volume
        vol += b.volume
        out.append(pv / vol if vol else None)
    return out


def obv(bars):
    out, total = [0.0], 0.0
    for i in range(1, len(bars)):
        total += bars[i].volume if bars[i].close > bars[i - 1].close else -bars[i].volume if bars[i].close < bars[i - 1].close else 0.0
        out.append(total)
    return out[: len(bars)]
