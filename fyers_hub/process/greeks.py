"""Black-Scholes price, implied volatility aur greeks (pure python, koi scipy nahi)."""
from __future__ import annotations

import math

_SQ2PI = math.sqrt(2 * math.pi)


def _cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2)))


def _pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / _SQ2PI


def _d1d2(S, K, T, r, q, sigma):
    sq = sigma * math.sqrt(T)
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / sq
    return d1, d1 - sq


def bs_price(S, K, T, r, q, sigma, is_call: bool) -> float:
    if T <= 0 or sigma <= 0:
        return max(0.0, (S - K) if is_call else (K - S))
    d1, d2 = _d1d2(S, K, T, r, q, sigma)
    if is_call:
        return S * math.exp(-q * T) * _cdf(d1) - K * math.exp(-r * T) * _cdf(d2)
    return K * math.exp(-r * T) * _cdf(-d2) - S * math.exp(-q * T) * _cdf(-d1)


def implied_vol(price, S, K, T, r, q, is_call: bool, lo=1e-4, hi=5.0, tol=1e-6) -> float | None:
    if not (price and price > 0 and S > 0 and K > 0 and T > 0):
        return None
    intrinsic = max(0.0, (S * math.exp(-q * T) - K * math.exp(-r * T)) if is_call
                    else (K * math.exp(-r * T) - S * math.exp(-q * T)))
    if price < intrinsic - 1e-9 or bs_price(S, K, T, r, q, hi, is_call) < price:
        return None
    for _ in range(80):  # bisection - hamesha converge karta hai
        mid = 0.5 * (lo + hi)
        if bs_price(S, K, T, r, q, mid, is_call) > price:
            hi = mid
        else:
            lo = mid
        if hi - lo < tol:
            break
    return 0.5 * (lo + hi)


def greeks(S, K, T, r, q, sigma, is_call: bool) -> dict:
    """delta, gamma, theta (per calendar din), vega (per 1 vol-point), rho (per 1% rate)."""
    d1, d2 = _d1d2(S, K, T, r, q, sigma)
    eq, er, sq = math.exp(-q * T), math.exp(-r * T), math.sqrt(T)
    pdf = _pdf(d1)
    gamma = eq * pdf / (S * sigma * sq)
    vega = S * eq * pdf * sq / 100.0
    if is_call:
        delta = eq * _cdf(d1)
        theta = (-S * eq * pdf * sigma / (2 * sq) - r * K * er * _cdf(d2) + q * S * eq * _cdf(d1)) / 365.0
        rho = K * T * er * _cdf(d2) / 100.0
    else:
        delta = -eq * _cdf(-d1)
        theta = (-S * eq * pdf * sigma / (2 * sq) + r * K * er * _cdf(-d2) - q * S * eq * _cdf(-d1)) / 365.0
        rho = -K * T * er * _cdf(-d2) / 100.0
    return {"delta": delta, "gamma": gamma, "theta": theta, "vega": vega, "rho": rho}
