import math


def _cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def _pdf(x):
    return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)


def _d(S, K, T, r, sigma):
    if S <= 0 or K <= 0 or T <= 0 or sigma <= 0:
        raise ValueError("S, K, T, sigma > 0 hone chahiye")
    d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))
    return d1, d1 - sigma * math.sqrt(T)


def price(S, K, T, r, sigma, kind="call"):
    d1, d2 = _d(S, K, T, r, sigma)
    if kind == "call":
        return S * _cdf(d1) - K * math.exp(-r * T) * _cdf(d2)
    return K * math.exp(-r * T) * _cdf(-d2) - S * _cdf(-d1)


def delta(S, K, T, r, sigma, kind="call"):
    d1, _ = _d(S, K, T, r, sigma)
    return _cdf(d1) if kind == "call" else _cdf(d1) - 1


def gamma(S, K, T, r, sigma):
    d1, _ = _d(S, K, T, r, sigma)
    return _pdf(d1) / (S * sigma * math.sqrt(T))


def vega(S, K, T, r, sigma):
    d1, _ = _d(S, K, T, r, sigma)
    return S * _pdf(d1) * math.sqrt(T)
