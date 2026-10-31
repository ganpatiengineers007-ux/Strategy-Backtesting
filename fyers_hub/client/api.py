"""Fyers REST wrapper: rate-limit + retry + token auto-refresh. Baaki system seedha Fyers ko nahi bulata."""
from __future__ import annotations

import time
from datetime import date
from typing import Any

from fyers_hub.auth import flow
from fyers_hub.client.limiter import RateLimiter
from fyers_hub.settings import Settings, get_settings

Candle = tuple  # (ts, open, high, low, close, volume)


class ApiError(Exception):
    pass


class TokenError(ApiError):
    pass


def _is_auth_error(resp: dict) -> bool:
    code = resp.get("code")
    msg = str(resp.get("message", "")).lower()
    return code in (-16, -15, -8, 401, 403) or "token" in msg or "authenticate" in msg


class FyersApi:
    def __init__(self, settings: Settings | None = None, limiter: RateLimiter | None = None,
                 model: Any = None, retries: int = 4, backoff: float = 1.5, sleep=time.sleep):
        self.s = settings or get_settings()
        self.limiter = limiter or RateLimiter(self.s.max_per_sec, self.s.max_per_min)
        self._model = model
        self._injected = model is not None
        self.retries, self.backoff, self._sleep = retries, backoff, sleep

    # ---- model (SDK) ----
    def _build_model(self, force_refresh: bool = False):
        if self._injected:
            return self._model
        try:
            from fyers_apiv3 import fyersModel
        except ImportError as e:
            raise ApiError("fyers-apiv3 install nahi hai: pip install fyers-apiv3") from e
        tok = flow.ensure_token(self.s, force_refresh=force_refresh)
        self.s.log_dir.mkdir(parents=True, exist_ok=True)
        self._model = fyersModel.FyersModel(
            client_id=self.s.app_id, token=tok.access_token, is_async=False, log_path=str(self.s.log_dir)
        )
        return self._model

    @property
    def model(self):
        return self._model or self._build_model()

    # ---- core call ----
    def _call(self, name: str, *args, **kw) -> dict:
        refreshed = False
        last: dict = {}
        for attempt in range(self.retries + 1):
            self.limiter.acquire()
            try:
                resp = getattr(self.model, name)(*args, **kw)
            except Exception as e:  # noqa: BLE001 - network etc.
                resp = {"s": "error", "message": str(e)}
            last = resp if isinstance(resp, dict) else {"s": "error", "message": "bad response"}
            if last.get("s") in ("ok", "no_data"):
                return last
            if _is_auth_error(last) and not refreshed and not self._injected:
                refreshed = True
                try:
                    self._model = self._build_model(force_refresh=True)
                    continue
                except flow.AuthError as e:
                    raise TokenError(str(e)) from None
            if _is_auth_error(last):
                raise TokenError(last.get("message", "token error"))
            self._sleep(self.backoff ** (attempt + 1))
        raise ApiError(f"{name} fail: {last.get('message') or last}")

    # ---- endpoints ----
    def history(self, symbol: str, tf: str, start: date, end: date) -> list[Candle]:
        resp = self._call(
            "history",
            data={"symbol": symbol, "resolution": tf, "date_format": "1",
                  "range_from": start.isoformat(), "range_to": end.isoformat(), "cont_flag": "1"},
        )
        out = []
        for c in resp.get("candles") or []:
            out.append((int(c[0]), float(c[1]), float(c[2]), float(c[3]), float(c[4]), float(c[5] if len(c) > 5 else 0)))
        return out

    def quotes(self, symbols: list[str]) -> list[dict]:
        out: list[dict] = []
        for i in range(0, len(symbols), 50):  # Fyers: ek call me 50 symbols tak
            resp = self._call("quotes", data={"symbols": ",".join(symbols[i:i + 50])})
            for item in resp.get("d") or []:
                v = item.get("v") or {}
                if item.get("s") != "ok" or not isinstance(v, dict):
                    continue
                out.append({
                    "symbol": item.get("n") or v.get("symbol"),
                    "ltp": v.get("lp"), "open": v.get("open_price"), "high": v.get("high_price"),
                    "low": v.get("low_price"), "prev_close": v.get("prev_close_price"),
                    "volume": v.get("volume"), "change_pct": v.get("chp"),
                    "bid": v.get("bid"), "ask": v.get("ask"), "ts_exchange": v.get("tt"),
                })
        return out

    def option_chain(self, symbol: str, strikecount: int = 10, expiry_ts: str | int = "") -> dict:
        resp = self._call("optionchain", data={"symbol": symbol, "strikecount": strikecount,
                                               "timestamp": str(expiry_ts) if expiry_ts else ""})
        return resp.get("data") or {}

    def profile(self) -> dict:
        return self._call("get_profile")
