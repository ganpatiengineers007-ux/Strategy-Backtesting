"""Normalizer tests: base OHLCV plus JSON option-chain extras."""
import json

from data.normalizer import normalize


def test_normalize_base_fields_and_numeric_extras():
    bars = normalize([{"ts": "2026-01-01T09:15:00", "open": "100", "high": "101",
                       "low": "99", "close": "100.5", "volume": "1000", "oi": "5000"}])
    assert bars[0].close == 100.5
    assert bars[0].extras["oi"] == 5000.0


def test_option_chain_json_is_parsed():
    chain = [{"strike": 100, "opt_type": "CE", "gamma": 0.02, "oi": 60000, "iv": 0.15}]
    bars = normalize([{"ts": "2026-01-01T09:15:00", "open": "100", "high": "101",
                       "low": "99", "close": "100.5", "volume": "1000", "oi": "5000",
                       "option_chain": json.dumps(chain)}])
    assert bars[0].extras["option_chain"] == chain


def test_invalid_option_chain_stays_string():
    bars = normalize([{"ts": "2026-01-01T09:15:00", "open": "100", "high": "101",
                       "low": "99", "close": "100.5", "volume": "1000",
                       "option_chain": "not-json"}])
    assert bars[0].extras["option_chain"] == "not-json"
