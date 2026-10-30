def sma(values, n):
    out, s = [None] * len(values), 0.0
    for i, v in enumerate(values):
        s += v
        if i >= n:
            s -= values[i - n]
        if i >= n - 1:
            out[i] = s / n
    return out


def ema(values, n):
    out, k, prev = [None] * len(values), 2.0 / (n + 1), None
    for i, v in enumerate(values):
        if i == n - 1:
            prev = sum(values[:n]) / n
            out[i] = prev
        elif i >= n:
            prev = v * k + prev * (1 - k)
            out[i] = prev
    return out
