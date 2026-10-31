import json
import os
import stat
import time

import pytest

from fyers_hub.auth import flow
from fyers_hub.auth.store import Token, load_token, next_expiry, save_token
from fyers_hub.client.limiter import RateLimiter
from fyers_hub.settings import get_settings


def test_limiter_blocks_over_limit():
    clock = [0.0]
    slept = []

    def sleep(x):
        slept.append(x)
        clock[0] += x

    lim = RateLimiter(2, 100, clock=lambda: clock[0], sleep=sleep)
    for _ in range(5):
        lim.acquire()
    assert slept and sum(slept) >= 1.0  # 5 call, 2/sec => kam se kam 1+ sec ruka


def test_token_file_perm_and_roundtrip(tmp_path):
    p = tmp_path / "t" / "token.json"
    tok = Token("AAA", "RRR", "APP", 1, 2)
    save_token(p, tok)
    assert load_token(p) == tok
    assert stat.S_IMODE(os.stat(p).st_mode) == 0o600


def test_next_expiry_is_future():
    assert next_expiry() > time.time()


def env(monkeypatch, pin="1234"):
    monkeypatch.setenv("FYERS_APP_ID", "APP-100")
    monkeypatch.setenv("FYERS_SECRET_KEY", "SECRET")
    monkeypatch.setenv("FYERS_PIN", pin)
    return get_settings()


def test_login_url_and_parse(monkeypatch):
    s = env(monkeypatch)
    url = flow.login_url(s)
    assert "client_id=APP-100" in url and "generate-authcode" in url and "SECRET" not in url
    state = (s.home / "pending_state").read_text()
    assert flow.parse_auth_code(f"https://x/redirect?s=ok&auth_code=CODE1&state={state}", s) == "CODE1"
    assert flow.parse_auth_code("RAWCODE", s) == "RAWCODE"
    with pytest.raises(flow.AuthError):
        flow.parse_auth_code("https://x/redirect?auth_code=C&state=WRONG", s)
    with pytest.raises(flow.AuthError):
        flow.parse_auth_code("https://x/redirect?nothing=1", s)


def test_exchange_refresh_ensure(monkeypatch):
    s = env(monkeypatch)
    calls = []

    def post(url, payload):
        calls.append((url, payload))
        if "validate-authcode" in url:
            return {"s": "ok", "access_token": "ACC1", "refresh_token": "REF1"}
        return {"s": "ok", "access_token": "ACC2"}

    tok = flow.exchange_code("CODE", s, post)
    assert tok.access_token == "ACC1" and calls[0][1]["appIdHash"] == flow.app_hash("APP-100", "SECRET")
    assert flow.ensure_token(s, post).access_token == "ACC1"  # valid hai, naya call nahi
    assert len(calls) == 1
    t2 = flow.ensure_token(s, post, force_refresh=True)
    assert t2.access_token == "ACC2" and t2.refresh_token == "REF1"
    assert calls[1][1]["pin"] == "1234"


def test_refresh_without_pin_needs_login(monkeypatch):
    s = env(monkeypatch, pin="")
    save_token(s.token_path, Token("A", "R", "APP-100", 0, 1))  # expire ho chuka
    with pytest.raises(flow.NeedsLogin):
        flow.ensure_token(s, lambda u, p: {})


def test_exchange_failure_message(monkeypatch):
    s = env(monkeypatch)
    with pytest.raises(flow.AuthError):
        flow.exchange_code("BAD", s, lambda u, p: {"s": "error", "message": "invalid code"})
    assert load_token(s.token_path) is None
