"""Fyers login + token: auth-url -> auth_code -> access_token (+ refresh_token se 15 din tak auto-refresh)."""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Callable

from fyers_hub.auth.store import Token, load_token, next_expiry, save_token
from fyers_hub.settings import Settings, get_settings

AUTH_BASE = "https://api-t1.fyers.in/api/v3"


class AuthError(Exception):
    pass


class NeedsLogin(AuthError):
    """Token nahi/expire - `python -m fyers_hub auth` chalao."""


def _post_json(url: str, payload: dict, timeout: int = 20) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:  # Fyers error body bhi JSON deta hai
        try:
            return json.loads(e.read().decode())
        except Exception:
            raise AuthError(f"HTTP {e.code} from Fyers") from None
    except (urllib.error.URLError, TimeoutError) as e:
        raise AuthError(f"Network error: {e}") from None


def app_hash(app_id: str, secret: str) -> str:
    return hashlib.sha256(f"{app_id}:{secret}".encode()).hexdigest()


def _state_path(s: Settings):
    return s.home / "pending_state"


def login_url(s: Settings | None = None) -> str:
    s = s or get_settings()
    s.require_app()
    state = secrets.token_urlsafe(16)
    s.home.mkdir(parents=True, exist_ok=True)
    _state_path(s).write_text(state)
    q = urllib.parse.urlencode(
        {"client_id": s.app_id, "redirect_uri": s.redirect_uri, "response_type": "code", "state": state}
    )
    return f"{AUTH_BASE}/generate-authcode?{q}"


def parse_auth_code(text: str, s: Settings | None = None) -> str:
    """Poora redirect URL ya sirf auth_code - dono chalega."""
    text = text.strip()
    if "auth_code=" not in text and "://" not in text:
        return text
    qs = urllib.parse.parse_qs(urllib.parse.urlparse(text).query)
    code = (qs.get("auth_code") or [""])[0]
    if not code:
        raise AuthError("URL me auth_code nahi mila. Login ke baad ka poora URL paste karo.")
    got_state = (qs.get("state") or [""])[0]
    if s is not None and _state_path(s).is_file() and got_state:
        if not hmac.compare_digest(_state_path(s).read_text().strip(), got_state):
            raise AuthError("state match nahi hua - naya login URL banao (auth-url).")
    return code


def _token_from(resp: dict, app_id: str, old_refresh: str = "") -> Token:
    if resp.get("s") != "ok" or not resp.get("access_token"):
        raise AuthError(f"Fyers ne token nahi diya: {resp.get('message') or resp.get('s')}")
    now = int(time.time())
    return Token(
        access_token=resp["access_token"],
        refresh_token=resp.get("refresh_token") or old_refresh,
        app_id=app_id,
        issued_at=now,
        expires_at=next_expiry(now),
    )


def exchange_code(auth_code: str, s: Settings | None = None, post: Callable = _post_json) -> Token:
    s = s or get_settings()
    s.require_app()
    resp = post(
        f"{AUTH_BASE}/validate-authcode",
        {"grant_type": "authorization_code", "appIdHash": app_hash(s.app_id, s.secret_key), "code": auth_code},
    )
    tok = _token_from(resp, s.app_id)
    save_token(s.token_path, tok)
    return tok


def refresh(s: Settings | None = None, post: Callable = _post_json) -> Token:
    s = s or get_settings()
    s.require_app()
    old = load_token(s.token_path)
    if not old or not old.refresh_token:
        raise NeedsLogin("refresh_token nahi hai - auth chalao.")
    if not s.pin:
        raise NeedsLogin("FYERS_PIN set nahi hai - auto-refresh nahi ho sakta, auth chalao.")
    resp = post(
        f"{AUTH_BASE}/validate-refresh-token",
        {
            "grant_type": "refresh_token",
            "appIdHash": app_hash(s.app_id, s.secret_key),
            "refresh_token": old.refresh_token,
            "pin": s.pin,
        },
    )
    try:
        tok = _token_from(resp, s.app_id, old.refresh_token)
    except AuthError as e:
        raise NeedsLogin(f"refresh fail: {e}") from None
    save_token(s.token_path, tok)
    return tok


def ensure_token(s: Settings | None = None, post: Callable = _post_json, force_refresh: bool = False) -> Token:
    s = s or get_settings()
    tok = load_token(s.token_path)
    if tok and tok.app_id == s.app_id and tok.valid() and not force_refresh:
        return tok
    return refresh(s, post)
