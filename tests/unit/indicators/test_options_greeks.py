import math

from indicators import options_greeks as g


def test_put_call_parity_and_greek_signs():
    S, K, T, r, s = 100.0, 100.0, 0.5, 0.05, 0.2
    c, p = g.price(S, K, T, r, s, "call"), g.price(S, K, T, r, s, "put")
    assert abs((c - p) - (S - K * math.exp(-r * T))) < 1e-9
    assert 0 < g.delta(S, K, T, r, s) < 1 and -1 < g.delta(S, K, T, r, s, "put") < 0
    assert g.gamma(S, K, T, r, s) > 0 and g.vega(S, K, T, r, s) > 0
