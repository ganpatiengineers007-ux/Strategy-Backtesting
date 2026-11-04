#!/usr/bin/env python3
"""
build_production_fixes.py
=========================
Strategy-Backtesting repo ke liye production fixes EK hi run me generate karta hai.

Kya karta hai:
  1. Asli repo ko kabhi touch nahi karta. Pehle ek alag copy me sab kaam hota hai.
  2. Har fix ek exact "old -> new" patch hai. Patch tabhi lagta hai jab:
       - old text file me theek 1 baar mile (galat jagah patch nahi lagta)
       - marker pehle se maujood na ho (dobara chalane par double-apply nahi hota)
     Koi bhi patch fail ho to KUCH BHI likha nahi jaata (all-or-nothing).
  3. Naye files likhta hai: Docker, compose, nginx, CI, requirements-prod, .dockerignore,
     cleanup script, aur fix-tests (tests/unit/fixes).
  4. Sab changed .py files compile check karta hai. --verify ho to fix-tests bhi chalata hai.
  5. Output: <out>/repo (patched copy), <out>/bundle.zip (sirf changed files),
     <out>/manifest.json (sha256), <out>/backup (originals), <out>/PRODUCTION_FIXES.md.

Usage:
  python build_production_fixes.py --repo /path/Strategy-Backtesting-main --out ./fixes_out
  python build_production_fixes.py --repo ... --out ... --verify      # tests bhi chalao
  python build_production_fixes.py --repo ... --dry-run               # sirf report dikhao

Exit codes: 0 = ok, 1 = patch/compile/verify fail, 2 = galat input.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger("build_fixes")

REPO_MARKERS = (
    "pyproject.toml",
    "backend/app.py",
    "fyers_hub/cli.py",
    "registry/registry.py",
    "backtest/engine.py",
)
COPY_IGNORE = shutil.ignore_patterns(
    ".git", "__pycache__", ".pytest_cache", "node_modules", "runs", ".venv", "venv", "*.pyc"
)


class PatchError(RuntimeError):
    pass


@dataclass(frozen=True)
class Patch:
    pid: str
    path: str       # repo ke andar relative path
    old: str        # ye text file me theek 1 baar hona chahiye
    new: str        # replacement
    marker: str     # ye text maujood ho to patch pehle se lag chuka hai
    note: str


@dataclass(frozen=True)
class NewFile:
    pid: str
    path: str       # new ya overwrite (overwrite par backup banta hai)
    content: str
    note: str
    executable: bool = False


@dataclass
class Result:
    pid: str
    path: str
    kind: str       # patch | file
    status: str     # applied | already | created | overwritten | unchanged | FAIL
    note: str


# ----------------------------------------------------------------------------
# 1) PATCHES: existing files me chhote, exact badlaav
# ----------------------------------------------------------------------------

APP_HELPERS = r'''def _is_production():
    return os.environ.get("SVL_ENV", "").strip().lower() in ("production", "prod")


def _enforce_production_settings():
    """Production me API_KEY khaali ho to app start hi na ho (khula API nahi chalega)."""
    import logging

    if _is_production() and not os.environ.get("API_KEY", "").strip():
        raise RuntimeError("SVL_ENV=production hai par API_KEY khaali hai - API_KEY set karo")
    if _is_production() and os.environ.get("RUN_ISOLATED") != "1":
        logging.getLogger("backend").warning("RUN_ISOLATED=1 nahi hai - strategy code API process me chalega")


def _cors_origins():
    return [o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()]


def _add_cors(app):
    origins = _cors_origins()
    if not origins:
        return
    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-API-Key"],
    )


'''

LIVE_HELPER = r'''def safe_since(tf, now):
    """derive() ke liye since_ts. Purana window (now - 3 din) candles kharab karta tha.

    Minute/second tf: din ki shuruaat se. Session open (09:15) se pehle koi candle nahi hoti,
    isliye din ke andar ke sab bucket poore rahte hain. Daily-based tf (jaise 15D): None = poori
    history, kyunki adhoora window ka block pehle se saved candle ko overwrite karta tha.
    """
    if parse_tf(tf)[0] == "d":
        return None
    return day_start_epoch(ist_date(now))


'''

CLI_HELPER = r'''def _export_rows(rows):
    """Hub ka epoch ts ISO IST me likho - data/loaders ISO timestamp hi maanta hai."""
    for r in rows:
        yield (datetime.fromtimestamp(int(r[0]), IST).strftime("%Y-%m-%dT%H:%M:%S"),) + tuple(r[1:])


'''

SWEEP_ENTRY_NEW = r'''oid = self._order("BUY" if side == "LONG" else "SELL", qty, f"entry-{level_name}")
        if oid is None:
            log.error("entry broker ne reject kiya - position record NAHI ki (orderbook check karo)")
            return'''

SWEEP_EXIT_NEW = r'''oid = self._order("SELL" if p["side"] == "LONG" else "BUY", p["qty"], why)
        if oid is None:
            log.error(f"EXIT reject ({why}) - position khuli rakhi, {RETRY_COOLDOWN_SEC}s baad retry")
            self._retry_after = time.time() + RETRY_COOLDOWN_SEC
            return'''

SWEEP_TICK_NEW = r'''if time.time() < self._retry_after:
                return          # reject hui exit ka cooldown
            if ts.time() >= SQUARE_OFF:
                self._exit(ltp, "eod-square-off")
                return
            self._manage(ltp, ts)'''

ENGINE_EXIT_BLOCK = r'''if exit_pending and pf.position is not None:
            close(bar.open, bar, "SIGNAL_EXIT")   # EXIT agle bar ke open par (lookahead nahi)
        exit_pending = False
        ex = model.check_exit(pf.position, bar)'''

PATCHES: list[Patch] = [
    # ---- backend: production guard + CORS ----
    Patch("P01", "backend/app.py", "def create_app():", APP_HELPERS + "def create_app():",
          "def _enforce_production_settings", "production me API_KEY zaroori; CORS helper"),
    Patch("P02", "backend/app.py", 'app = FastAPI(title="strategy-validation-lab")',
          '_enforce_production_settings()\n    app = FastAPI(title="strategy-validation-lab")\n    _add_cors(app)',
          "    _add_cors(app)", "startup par production check + CORS_ORIGINS se CORS"),
    # ---- fyers hub ----
    Patch("P03", "fyers_hub/client/api.py", 'or "token" in msg',
          'or "invalid token" in msg or "token expired" in msg',
          "invalid token", "auth error detection: 'token' substring hata kar specific phrases"),
    Patch("P04", "fyers_hub/ingest/ws.py", '        log = logging.getLogger("fyers_hub.ingest.ws")',
          '        _log = logging.getLogger("fyers_hub.ingest.ws")',
          "_log = logging.getLogger", "except me 'log' shadowing hatao (callbacks TypeError se bachein)"),
    Patch("P05", "fyers_hub/ingest/ws.py", '        log.exception("WebSocket keep_running error")',
          '        _log.exception("WebSocket keep_running error")',
          "_log.exception", "P04 ke saath"),
    Patch("P06", "fyers_hub/ingest/live.py", "from fyers_hub.process.resample import derive",
          "from fyers_hub.process.resample import derive, parse_tf",
          "derive, parse_tf", "parse_tf import (safe_since ke liye)"),
    Patch("P07", "fyers_hub/ingest/live.py", "from fyers_hub.timeutil import ist_date, is_market_open",
          "from fyers_hub.timeutil import ist_date, is_market_open, day_start_epoch",
          "day_start_epoch", "day_start_epoch import"),
    Patch("P08", "fyers_hub/ingest/live.py", "def run_live(", LIVE_HELPER + "def run_live(",
          "def safe_since", "safe_since helper (candle corruption fix)"),
    Patch("P09", "fyers_hub/ingest/live.py", "derive(conn, s, tf, since_ts=int(t) - 3 * 86400)",
          "derive(conn, s, tf, since_ts=safe_since(tf, t))",
          "safe_since(tf, t)", "3-din window hata kar safe_since (volume/OHLC corruption fix)"),
    Patch("P10", "fyers_hub/cli.py", "from datetime import date, timedelta",
          "from datetime import date, datetime, timedelta", "date, datetime, timedelta", "datetime import"),
    Patch("P11", "fyers_hub/cli.py",
          "from fyers_hub.settings import DEFAULT_BASE_TFS, DEFAULT_DERIVED_TFS, get_settings, read_symbol_file",
          "from fyers_hub.settings import DEFAULT_BASE_TFS, DEFAULT_DERIVED_TFS, get_settings, read_symbol_file\n"
          "from fyers_hub.timeutil import IST",
          "from fyers_hub.timeutil import IST", "IST import"),
    Patch("P12", "fyers_hub/cli.py", "def cmd_export(a, s):", CLI_HELPER + "def cmd_export(a, s):",
          "def _export_rows", "export helper (ISO IST timestamp)"),
    Patch("P13", "fyers_hub/cli.py", "w.writerows(hub.candles(a.symbol, a.tf, a.start, a.end))",
          "w.writerows(_export_rows(hub.candles(a.symbol, a.tf, a.start, a.end)))",
          "_export_rows(hub", "export ab ISO timestamp likhta hai (backtest loader compatible)"),
    # ---- backtest engine: exit agle bar ke open par ----
    Patch("P14", "backtest/engine.py",
          'bars, pending, rejections, status, reason = dataset.bars, None, [], "COMPLETED", ""',
          'bars, pending, rejections, status, reason = dataset.bars, None, [], "COMPLETED", ""\n'
          "    exit_pending = False",
          "exit_pending = False", "exit_pending flag init"),
    Patch("P15", "backtest/engine.py", "ex = model.check_exit(pf.position, bar)", ENGINE_EXIT_BLOCK,
          "if exit_pending and pf.position", "pending EXIT agle bar ke open par bharo"),
    Patch("P16", "backtest/engine.py", 'close(bar.close, bar, "SIGNAL_EXIT")', "exit_pending = True",
          "exit_pending = True", "signal EXIT ab same-bar close par nahi bharta (lookahead fix)"),
    # ---- live sweep trader: order-state bug ----
    Patch("P17", "scripts/sweep_strategy.py", "dtime(15, 20)",
          "dtime(15, 20)\nRETRY_COOLDOWN_SEC = 2.0   # exit reject hone par itne sec baad dobara koshish",
          "RETRY_COOLDOWN_SEC", "retry cooldown constant"),
    Patch("P18", "scripts/sweep_strategy.py", "self.atr = 0.0",
          "self.atr = 0.0\n        self._retry_after = 0.0",
          "self._retry_after = 0.0", "retry state init"),
    Patch("P19", "scripts/sweep_strategy.py",
          'self._order("BUY" if side == "LONG" else "SELL", qty, f"entry-{level_name}")',
          SWEEP_ENTRY_NEW, 'oid = self._order("BUY"', "entry reject hone par position record na ho"),
    Patch("P20", "scripts/sweep_strategy.py", 'return ""', "return None  # broker ne order reject kiya",
          "broker ne order reject kiya", "_order failure ab None (empty string nahi)"),
    Patch("P21", "scripts/sweep_strategy.py",
          'self._order("SELL" if p["side"] == "LONG" else "BUY", p["qty"], why)',
          SWEEP_EXIT_NEW, 'oid = self._order("SELL" if p["side"]', "exit reject hone par position khuli rakho"),
    Patch("P22", "scripts/sweep_strategy.py", "self._manage(ltp, ts)", SWEEP_TICK_NEW,
          "time.time() < self._retry_after", "exit retry cooldown + EOD square-off retry"),
]


# ----------------------------------------------------------------------------
# 2) NEW / OVERWRITE FILES
# ----------------------------------------------------------------------------

REGISTRY_PY = r'''"""Registry entry point: manifests discover, validate, strategy load.

Production fix: ek kharab manifest se poori registry ab nahi girti. Kharab strategy
self.errors me record hoti hai aur baaki strategies chalti rehti hain.
"""
import importlib
import logging
from pathlib import Path

from registry import compatibility
from registry.metadata import load_manifest
from registry.versioning import source_hash as _hash
from strategies.validation import validate_manifest

log = logging.getLogger("registry")


class Registry:
    def __init__(self, strategies_dir=None):
        self.dir = Path(strategies_dir) if strategies_dir else Path(__file__).resolve().parent.parent / "strategies"
        self.records = {}
        self.errors = {}

    def discover(self):
        self.records.clear()
        self.errors.clear()
        for d in sorted(self.dir.iterdir()):
            mf = d / "manifest.yaml"
            if not (d.is_dir() and mf.exists()):
                continue
            try:
                m = load_manifest(mf)
                errs = validate_manifest(m) + compatibility.check(m)
                if errs:
                    raise ValueError(f"invalid manifest: {errs}")
                sid = m["id"]
                if sid in self.records:
                    raise ValueError(f"duplicate strategy id: {sid}")
                self.records[sid] = {"manifest": m, "dir": d}
            except Exception as e:  # noqa: BLE001 - ek kharab strategy poori registry na roke
                self.errors[d.name] = f"{type(e).__name__}: {e}"
                log.error("strategy %s skip: %s", d.name, self.errors[d.name])
        return sorted(self.records)

    def _rec(self, sid):
        if sid not in self.records:
            self.discover()
        if sid not in self.records:
            hint = f" (manifest error: {self.errors[sid]})" if sid in self.errors else ""
            raise KeyError(f"unknown strategy: {sid}{hint}")
        return self.records[sid]

    def manifest(self, sid):
        return self._rec(sid)["manifest"]

    def load(self, sid, params=None):
        m = self._rec(sid)["manifest"]
        mod, cls = m["entry_point"].split(":")
        merged = dict(m.get("parameters") or {})
        merged.update(params or {})
        return getattr(importlib.import_module(mod), cls)(merged)

    def source_hash(self, sid):
        return _hash(self._rec(sid)["dir"])
'''

CLIENT_TS = r'''// API client. Production: API key sessionStorage se jaati hai (bundle me hardcode nahi).
// Base URL build-time env VITE_API_BASE se (docker build me /api). Dev me default localhost:8000.
const BASE: string = (import.meta as any).env?.VITE_API_BASE ?? "http://localhost:8000";
const KEY_NAME = "svl_api_key";

export function setApiKey(key: string): void {
  try {
    sessionStorage.setItem(KEY_NAME, key.trim());
  } catch {
    /* storage band ho to key sirf is page session me nahi rahegi */
  }
}

function headers(extra: Record<string, string> = {}): Record<string, string> {
  const h: Record<string, string> = { ...extra };
  try {
    const k = sessionStorage.getItem(KEY_NAME);
    if (k) h["X-API-Key"] = k;
  } catch {
    /* ignore */
  }
  return h;
}

async function handle<T>(r: Response, label: string): Promise<T> {
  if (r.status === 401) throw new Error(`${label}: unauthorized (API key galat ya khaali)`);
  if (!r.ok) throw new Error(`${label} failed: ${r.status}`);
  return (await r.json()) as T;
}

export async function getJson<T>(path: string): Promise<T> {
  const r = await fetch(BASE + path, { headers: headers() });
  return handle<T>(r, `GET ${path}`);
}

export async function postJson<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(BASE + path, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
  });
  return handle<T>(r, `POST ${path}`);
}
'''

TEST_INIT = "# tests/unit/fixes - production fixes ke regression tests\n"

TEST_DERIVE = r'''"""Regression: windowed derive ab poore bucket nahi bigaadta (safe_since)."""
from datetime import date

from fyers_hub.ingest.live import safe_since
from fyers_hub.process.resample import derive
from fyers_hub.storage import db as dbm
from fyers_hub.timeutil import day_start_epoch


def _minute_rows(d, n=375, base=100.0):
    start = day_start_epoch(d) + 9 * 3600 + 15 * 60
    return [(start + i * 60, base + i, base + i + 1, base + i - 1, base + i, 10.0) for i in range(n)]


def test_windowed_derive_keeps_completed_buckets():
    conn = dbm.connect(":memory:")
    sym = "NSE:SBIN-EQ"
    d1, d2 = date(2026, 10, 12), date(2026, 10, 13)
    dbm.upsert_candles(conn, sym, "1", _minute_rows(d1) + _minute_rows(d2))
    derive(conn, sym, "30")
    q = "SELECT ts,open,high,low,close,volume FROM candles WHERE symbol=? AND tf='30' ORDER BY ts"
    snap = conn.execute(q, (sym,)).fetchall()
    now = day_start_epoch(d2) + 10 * 3600 + 7 * 60   # live loop jaisa mid-day time
    derive(conn, sym, "30", base="1", since_ts=safe_since("30", now))
    assert conn.execute(q, (sym,)).fetchall() == snap


def test_daily_based_tf_uses_full_history():
    conn = dbm.connect(":memory:")
    now = day_start_epoch(date(2026, 10, 13)) + 10 * 3600
    assert safe_since("15D", now) is None
    assert safe_since("D", now) is None
'''

TEST_EXPORT = r'''"""Regression: hub export ISO IST timestamp likhta hai (backtest loader ke saath compatible)."""
from data.timestamps import parse_ts
from fyers_hub import cli


def test_export_writes_iso_ist():
    rows = [(1791776700, 100.0, 101.0, 99.0, 100.0, 10.0)]   # 2026-10-12 09:15 IST
    out = list(cli._export_rows(rows))
    ts = out[0][0]
    assert ts == "2026-10-12T09:15:00", ts
    parse_ts(ts)   # raise nahi hona chahiye
    assert out[0][1:] == (100.0, 101.0, 99.0, 100.0, 10.0)
'''

TEST_SWEEP = r'''"""Regression: live sweep trader - order reject par position ki state galat na ho."""
import os
import sys
import types

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))


def _load_sweep():
    try:
        import dhanhq  # noqa: F401
    except ImportError:
        stub = types.ModuleType("dhanhq")

        class DhanContext:
            def __init__(self, *a, **k):
                pass

        class dhanhq_client:
            def __init__(self, ctx):
                pass

        class MarketFeed:
            NSE_FNO = "NSE_FNO"
            Quote = "Quote"

            def __init__(self, *a, **k):
                pass

        stub.DhanContext = DhanContext
        stub.dhanhq = dhanhq_client
        stub.MarketFeed = MarketFeed
        sys.modules["dhanhq"] = stub
    scripts = os.path.join(_REPO, "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    import sweep_strategy
    return sweep_strategy


class _FakeApi:
    def __init__(self, ok=True):
        self.ok = ok

    def place_order(self, **kw):
        if not self.ok:
            raise RuntimeError("RMS: margin kam hai")
        return {"orderId": "T1"}

    def historical_daily_data(self, **kw):
        raise RuntimeError("test: no history")


def _strategy(sw, api):
    sw.DRY_RUN = False
    sw.journal_trade = lambda *a, **k: None
    s = sw.SweepStrategy(api, depth=None)
    s.atr = 10.0
    return s


def test_rejected_entry_is_not_recorded():
    sw = _load_sweep()
    old = sw.DRY_RUN
    try:
        s = _strategy(sw, _FakeApi(ok=False))
        s._enter("LONG", 22000.0, 21980.0, "R22000")
        assert s.position is None
        assert s.trades_today == 0
    finally:
        sw.DRY_RUN = old


def test_accepted_entry_is_recorded():
    sw = _load_sweep()
    old = sw.DRY_RUN
    try:
        s = _strategy(sw, _FakeApi(ok=True))
        s._enter("LONG", 22000.0, 21980.0, "R22000")
        assert s.position is not None
        assert s.trades_today == 1
    finally:
        sw.DRY_RUN = old


def test_rejected_exit_keeps_position_and_sets_cooldown():
    sw = _load_sweep()
    old = sw.DRY_RUN
    try:
        api = _FakeApi(ok=True)
        s = _strategy(sw, api)
        s._enter("LONG", 22000.0, 21980.0, "R22000")
        assert s.position is not None
        api.ok = False
        s._exit(21975.0, "stop-loss")
        assert s.position is not None          # exit reject: position khuli hi rahni chahiye
        assert s.realized_pnl == 0.0           # galat PnL record nahi
        assert s._retry_after > 0
    finally:
        sw.DRY_RUN = old


def test_successful_exit_clears_position():
    sw = _load_sweep()
    old = sw.DRY_RUN
    try:
        s = _strategy(sw, _FakeApi(ok=True))
        s._enter("LONG", 22000.0, 21980.0, "R22000")
        s._exit(21975.0, "stop-loss")
        assert s.position is None
    finally:
        sw.DRY_RUN = old
'''

TEST_ENGINE = r'''"""Regression: EXIT signal agle bar ke open par bharta hai (same-bar close lookahead nahi)."""
from backtest.engine import run_backtest
from data.models import Bar, Dataset
from strategies.base import Strategy
from strategies.models import Signal


class _Scripted(Strategy):
    strategy_id = "scripted_test"
    required_data = ()

    def __init__(self, script):
        super().__init__({})
        self.script = script
        self.calls = 0

    def on_bar(self, ctx):
        sig = self.script.get(self.calls)
        self.calls += 1
        return sig


def _bars():
    raw = [  # open, high, low, close
        (100, 101, 99, 100),
        (100, 102, 99, 101),
        (101, 103, 100, 102),
        (102, 104, 101, 103),
        (105, 106, 104, 105),
        (106, 107, 105, 106),
    ]
    return [Bar(f"2026-10-12T09:{15 + i:02d}:00", o, h, l, c, 1000.0) for i, (o, h, l, c) in enumerate(raw)]


def test_exit_fills_at_next_bar_open():
    ds = Dataset("t", "TEST", "1", _bars(), quality_status="PASS")
    strat = _Scripted({0: Signal("BUY", stop_loss=90.0), 3: Signal("EXIT")})
    res = run_backtest(ds, strat, {"slippage_bps": 0.0, "fee_pct": 0.0})
    assert res.status == "COMPLETED", res.status
    assert len(res.trades) == 1, res.trades
    t = res.trades[0]
    assert t["exit_price"] == 105.0, t          # bar 4 ka open, bar 3 ka close (103) nahi
    assert t["reason"] == "SIGNAL_EXIT", t
'''

TEST_REGISTRY = r'''"""Regression: ek kharab manifest se poori registry nahi girti."""
import os
import shutil
import tempfile

from registry.registry import Registry


def test_bad_manifest_does_not_break_registry():
    tmp = tempfile.mkdtemp(prefix="reg_test_")
    try:
        bad = os.path.join(tmp, "bad_one")
        os.makedirs(bad)
        with open(os.path.join(bad, "manifest.yaml"), "w", encoding="utf-8") as f:
            f.write("id: bad_one\n")
        reg = Registry(strategies_dir=tmp)
        ids = reg.discover()
        assert ids == []
        assert "bad_one" in reg.errors
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
'''

TEST_APP = r'''"""Regression: production me API_KEY ke bina app start nahi hota."""
import os


def test_production_requires_api_key():
    try:
        import fastapi  # noqa: F401
    except ImportError:
        return  # fastapi is environment me nahi - ye test skip
    from backend.app import create_app

    keys = ("SVL_ENV", "API_KEY")
    saved = {k: os.environ.get(k) for k in keys}
    try:
        os.environ["SVL_ENV"] = "production"
        os.environ.pop("API_KEY", None)
        failed = False
        try:
            create_app()
        except RuntimeError:
            failed = True
        assert failed, "production me API_KEY bina start nahi hona chahiye"
        os.environ["API_KEY"] = "x" * 32
        assert create_app() is not None
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
'''

BACKEND_DOCKERFILE = r'''# Backend image (repo root se build): docker build -f infra/Dockerfile -t svl-backend .
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Non-root user (uid 10001)
RUN groupadd --system app && useradd --system --gid app --uid 10001 --home /app app

COPY requirements-prod.txt ./requirements-prod.txt
RUN pip install -r requirements-prod.txt

COPY . .
RUN mkdir -p /app/runs /app/data && chown -R app:app /app/runs

USER app
EXPOSE 8000

# --workers 1: job queue abhi in-memory hai (multi-worker par jobs ek process me hi dikhenge)
CMD ["uvicorn", "--factory", "backend.app:create_app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--proxy-headers"]
'''

FRONTEND_DOCKERFILE = r'''# Frontend image (repo root se build): docker build -f infra/Dockerfile.frontend -t svl-web .
FROM node:20-alpine AS build
WORKDIR /src/frontend
COPY frontend/package*.json ./
RUN if [ -f package-lock.json ]; then npm ci --no-audit --no-fund; else npm install --no-audit --no-fund; fi
COPY frontend/ ./
ARG VITE_API_BASE=/api
ENV VITE_API_BASE=$VITE_API_BASE
RUN npx vite build

FROM nginx:1.27-alpine
COPY infra/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /src/frontend/dist /usr/share/nginx/html
EXPOSE 80
'''

COMPOSE_YML = r'''# Production stack. Chalane se pehle infra/.env me API_KEY bharo (infra/.env.example dekho).
name: strategy-lab

services:
  backend:
    build:
      context: ..
      dockerfile: infra/Dockerfile
    restart: unless-stopped
    environment:
      SVL_ENV: production
      API_KEY: ${API_KEY:?API_KEY set karo (infra/.env me)}
      CORS_ORIGINS: ${CORS_ORIGINS:-}
      RUN_ISOLATED: "1"
      DATA_DIR: /app/data
      RUNS_ROOT: /app/runs
      DATABASE_URL: sqlite:////app/runs/svl.sqlite3
    volumes:
      - ../runs:/app/runs
      - ../data:/app/data:ro
    expose:
      - "8000"
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5).status == 200 else 1)"]
      interval: 30s
      timeout: 10s
      retries: 3

  web:
    build:
      context: ..
      dockerfile: infra/Dockerfile.frontend
      args:
        VITE_API_BASE: /api
    restart: unless-stopped
    depends_on:
      backend:
        condition: service_healthy
    ports:
      - "80:80"
'''

NGINX_CONF = r'''# Frontend static + /api reverse proxy. TLS host-level nginx (ya nginx.tls.conf.example) se lagta hai.
server {
    listen 80;
    server_name _;
    server_tokens off;

    client_max_body_size 10m;

    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;
    add_header Referrer-Policy strict-origin-when-cross-origin always;
    add_header Content-Security-Policy "default-src 'self'; connect-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'" always;

    root /usr/share/nginx/html;

    location /api/ {
        proxy_pass http://backend:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }

    location / {
        try_files $uri /index.html;
    }
}
'''

NGINX_TLS_EXAMPLE = r'''# Host par nginx (docker ke bahar) ke liye TLS block - certbot se cert lene ke baad use karo.
# Use: /etc/nginx/sites-available/svl ; phir: ln -s ... sites-enabled/ ; nginx -t && systemctl reload nginx
server {
    listen 80;
    server_name your-domain.example;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.example;

    ssl_certificate     /etc/letsencrypt/live/your-domain.example/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.example/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    location / {
        proxy_pass http://127.0.0.1:80;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
'''

INFRA_ENV_EXAMPLE = r'''# infra/.env - docker compose ise padhta hai. Ise commit mat karo.
API_KEY=replace-with-32-plus-random-chars
CORS_ORIGINS=https://your-domain.example
'''

DOCKERIGNORE = r'''.git
.github
.env
.env.*
.venv
venv
**/__pycache__
**/*.pyc
.pytest_cache
node_modules
frontend/node_modules
frontend/dist
runs
output
artifacts
archive
docs
*.zip
external/**/*.zip
**/token.json
*.sqlite3
*.db
data/**/*.csv
data/**/*.parquet
'''

REQUIREMENTS_PROD = r'''# Backend runtime (production / docker). fyers-apiv3 hub host par alag se lagta hai; dev tools (pytest) nahi.
fastapi>=0.100.0,<1.0
uvicorn>=0.23.0,<1.0
pydantic>=2.0.0,<3.0
httpx>=0.24.0,<1.0
pandas>=2.0.0,<3.0
numpy>=1.24.0,<3.0
pyarrow>=14.0.0,<30.0
PyYAML>=6.0.0,<7.0
python-dotenv>=1.0.0,<2.0
'''

CI_YML = r'''name: ci
on:
  push:
  pull_request:

jobs:
  python:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
      - run: pip install -r requirements-prod.txt pytest httpx
      - run: python -m pytest -q

  frontend:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: npm install --no-audit --no-fund
      - run: npx tsc --noEmit
      - run: npx vite build

  docker:
    runs-on: ubuntu-latest
    needs: [python]
    steps:
      - uses: actions/checkout@v4
      - run: docker build -f infra/Dockerfile -t svl-backend:ci .
      - run: docker build -f infra/Dockerfile.frontend -t svl-web:ci .
'''

CLEANUP_SH = r'''#!/usr/bin/env bash
# Repo ki safai. DEFAULT = DRY RUN (kuch delete nahi hota).
# Asli delete ke liye: ./scripts/cleanup_unused.sh --apply
set -euo pipefail
cd "$(dirname "$0")/.."

APPLY=0
if [ "${1:-}" = "--apply" ]; then APPLY=1; fi

TARGETS=(
  "Strategy-Backtesting-v3.zip"
  "Strategy-Backtesting-v4.zip"
  "Strategy-Backtesting-v8.zip"
  "fyers_hub.zip"
  "greeks_manifests.zip"
  "greeks_plugin.zip"
  "gts_lab_strategies (1).zip"
  "gts_lab_strategies (2).zip"
  "archive/gts_quant_lab.zip"
  "archive/quant_stat_arb_framework.zip"
  "scripts/bootstrap-5.py"
  "archive/bootstrap (4).py"
)

for t in "${TARGETS[@]}"; do
  if [ -e "$t" ]; then
    if [ $APPLY -eq 1 ]; then
      rm -f -- "$t" && echo "removed: $t"
    else
      echo "would remove: $t"
    fi
  fi
done

while IFS= read -r link; do
  if [ $APPLY -eq 1 ]; then
    rm -f -- "$link" && echo "removed broken symlink: $link"
  else
    echo "would remove broken symlink: $link"
  fi
done < <(find . -xtype l -not -path './.git/*')

echo "NOTE: root bootstrap.py aur scripts/bootstrap.py ko manually review karo (generator scripts hain)."
if [ $APPLY -ne 1 ]; then
  echo "Dry run tha. Asli delete ke liye: $0 --apply"
fi
'''

NEW_FILES: list[NewFile] = [
    NewFile("N01", "registry/registry.py", REGISTRY_PY, "bad manifest se poori registry na gire"),
    NewFile("N02", "frontend/src/api/client.ts", CLIENT_TS, "API key header + 401 message + VITE_API_BASE"),
    NewFile("N03", "tests/unit/fixes/__init__.py", TEST_INIT, "fix tests package"),
    NewFile("N04", "tests/unit/fixes/test_derive_window.py", TEST_DERIVE, "derive window regression"),
    NewFile("N05", "tests/unit/fixes/test_export_and_since.py", TEST_EXPORT, "export ISO regression"),
    NewFile("N06", "tests/unit/fixes/test_sweep_order_state.py", TEST_SWEEP, "sweep order-state regression"),
    NewFile("N07", "tests/unit/fixes/test_engine_exit_next_open.py", TEST_ENGINE, "engine exit regression"),
    NewFile("N08", "tests/unit/fixes/test_registry_resilience.py", TEST_REGISTRY, "registry regression"),
    NewFile("N09", "tests/unit/fixes/test_app_production_guard.py", TEST_APP, "production guard regression"),
    NewFile("N10", "infra/Dockerfile", BACKEND_DOCKERFILE, "non-root backend image, uvicorn CMD"),
    NewFile("N11", "infra/Dockerfile.frontend", FRONTEND_DOCKERFILE, "vite build + nginx static image"),
    NewFile("N12", "infra/docker-compose.yml", COMPOSE_YML, "backend + web, healthcheck, required API_KEY"),
    NewFile("N13", "infra/nginx.conf", NGINX_CONF, "/api proxy + security headers"),
    NewFile("N14", "infra/nginx.tls.conf.example", NGINX_TLS_EXAMPLE, "host-level TLS example"),
    NewFile("N15", "infra/.env.example", INFRA_ENV_EXAMPLE, "compose env template"),
    NewFile("N16", ".dockerignore", DOCKERIGNORE, "secrets, runs, zips build context se bahar"),
    NewFile("N17", "requirements-prod.txt", REQUIREMENTS_PROD, "runtime-only pinned ranges"),
    NewFile("N18", ".github/workflows/ci.yml", CI_YML, "pytest + frontend + docker build CI"),
    NewFile("N19", "scripts/cleanup_unused.sh", CLEANUP_SH, "dry-run default cleanup", executable=True),
]


# ----------------------------------------------------------------------------
# 3) ENGINE
# ----------------------------------------------------------------------------

def apply_patch(text: str, p: Patch) -> tuple[str, str]:
    """Return (new_text, status). status: applied | already. Galat ho to PatchError."""
    if p.marker in text:
        return text, "already"
    n = text.count(p.old)
    if n != 1:
        raise PatchError(f"{p.pid} {p.path}: old text {n} baar mila (theek 1 chahiye)")
    return text.replace(p.old, p.new, 1), "applied"


def sha256_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def check_repo(repo: Path) -> None:
    if not repo.is_dir():
        raise SystemExit(f"repo nahi mila: {repo}")
    missing = [m for m in REPO_MARKERS if not (repo / m).exists()]
    if missing:
        raise SystemExit(f"ye Strategy-Backtesting repo nahi lagta, missing: {missing}")


def plan(repo: Path) -> tuple[list[Result], dict[str, str], dict[str, bytes], list[str], set[str]]:
    """Memory me poori plan: results, files_to_write (text), originals, errors. Kuch likhta nahi."""
    results: list[Result] = []
    errors: list[str] = []
    originals: dict[str, bytes] = {}
    current: dict[str, str] = {}   # patch ke baad ka text
    for p in PATCHES:
        if p.path not in current:
            raw = (repo / p.path).read_bytes()
            originals[p.path] = raw
            current[p.path] = raw.decode("utf-8")
        try:
            current[p.path], status = apply_patch(current[p.path], p)
            results.append(Result(p.pid, p.path, "patch", status, p.note))
        except PatchError as e:
            errors.append(str(e))
            results.append(Result(p.pid, p.path, "patch", "FAIL", str(e)))

    files: dict[str, str] = {}
    for path, text in current.items():
        if text.encode("utf-8") != originals[path]:
            files[path] = text

    exec_paths: set[str] = set()
    for nf in NEW_FILES:
        target = repo / nf.path
        if nf.executable:
            exec_paths.add(nf.path)
        if target.exists():
            if target.read_text(encoding="utf-8") == nf.content:
                results.append(Result(nf.pid, nf.path, "file", "unchanged", nf.note))
                continue
            originals.setdefault(nf.path, target.read_bytes())
            results.append(Result(nf.pid, nf.path, "file", "overwritten", nf.note))
        else:
            results.append(Result(nf.pid, nf.path, "file", "created", nf.note))
        files[nf.path] = nf.content
    return results, files, originals, errors, exec_paths


def compile_check(root: Path, rel_paths: list[str]) -> list[str]:
    bad = []
    for rel in rel_paths:
        if not rel.endswith(".py"):
            continue
        src = (root / rel).read_text(encoding="utf-8")
        try:
            compile(src, rel, "exec")
        except SyntaxError as e:
            bad.append(f"{rel}:{e.lineno}: {e.msg}")
    return bad


def run_fix_tests(work: Path) -> tuple[str, str]:
    try:
        import pytest  # noqa: F401
    except ImportError:
        return "skipped", "pytest install nahi - tests/unit/fixes server par chalao"
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests/unit/fixes"],
        cwd=str(work), capture_output=True, text=True, timeout=900,
    )
    tail = (proc.stdout or proc.stderr).strip().splitlines()[-1:] or ["no output"]
    return ("passed" if proc.returncode == 0 else "FAILED"), tail[0]


def write_report(out: Path, results: list[Result], manifest: dict, verify_note: str, compile_bad: list[str]) -> None:
    lines = [
        "# Production fixes - build report",
        "",
        f"Generated: {manifest['generated_at']}",
        "",
        "## Patches aur files",
        "",
        "| ID | File | Kya hua | Status | Kyon |",
        "|---|---|---|---|---|",
    ]
    for r in results:
        lines.append(f"| {r.pid} | `{r.path}` | {r.kind} | {r.status} | {r.note} |")
    lines += [
        "",
        "## Verify",
        "",
        f"- Compile check: {'OK' if not compile_bad else 'FAIL: ' + '; '.join(compile_bad)}",
        f"- Fix tests: {verify_note}",
        "",
        "## Lagu karne ka kram (server par)",
        "",
        "1. `bundle.zip` ko repo me extract karo (ya `repo/` folder ko poori tarah use karo).",
        "2. `python -m pytest -q` chalao (fixture tests sahit).",
        "3. `infra/.env` banao: API_KEY aur CORS_ORIGINS bharo. Phir `docker compose -f infra/docker-compose.yml up -d --build`.",
        "4. Host par TLS: `infra/nginx.tls.conf.example` ko certbot ke baad lagao.",
        "5. Cleanup dekho: `./scripts/cleanup_unused.sh` (dry run). Theek lage to `--apply`.",
        "",
        "## Zaroori chetavani",
        "",
        "- Engine me EXIT ab agle bar ke open par bharta hai. Isse backtest ke numbers badlenge.",
        "  `tests/regression/test_known_results.py` aur `tests/fixtures/expected_results.json` ko naye numbers se update karna hoga (naye nateeje ko review karke).",
        "- Sweep trader ka `DRY_RUN = True` abhi bhi default hai. Live se pehle paper mode me chalao.",
        "- Broker orderbook se position reconciliation ka step manual hai (code me automatic nahi).",
        "- `_order` me agar broker orderId hi na de to use failure maana jata hai. Aise case me orderbook khud dekho.",
        "- Derived timeframes ke liye daily-based tf (15D) ab har minute poori history se banta hai. Symbols zyada hon to CPU dekho.",
        "",
        "## Rollback",
        "",
        "Har badle hue file ka original `backup/` me hai. Repo me wapas copy karo.",
        "",
    ]
    (out / "PRODUCTION_FIXES.md").write_text("\n".join(lines), encoding="utf-8")


def build(repo: Path, out: Path, verify: bool, dry_run: bool) -> int:
    check_repo(repo)
    results, files, originals, errors, exec_paths = plan(repo)

    print(f"{'ID':<5}{'STATUS':<12}{'FILE':<44}NOTE")
    for r in results:
        print(f"{r.pid:<5}{r.status:<12}{r.path:<44}{r.note}")

    if errors:
        print("\nFAIL - koi bhi file nahi likhi gayi (all-or-nothing):")
        for e in errors:
            print("  -", e)
        return 1
    if dry_run:
        print(f"\nDry run: {len(files)} file(s) badlti. Kuch likha nahi gaya.")
        return 0

    work = out / "repo"
    if work.exists():
        shutil.rmtree(work)
    out.mkdir(parents=True, exist_ok=True)
    # symlinks ko link hi rehne do (repo me gol-ghumne wale aur tootne wale links hain)
    shutil.copytree(repo, work, ignore=COPY_IGNORE, symlinks=True)

    backup = out / "backup"
    for rel, raw in originals.items():
        if rel in files:
            dst = backup / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(raw)

    for rel, text in files.items():
        dst = work / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(text, encoding="utf-8", newline="\n")
        if rel in exec_paths:
            os.chmod(dst, 0o755)

    changed = sorted(files)
    compile_bad = compile_check(work, changed)
    if compile_bad:
        print("\nCOMPILE FAIL:")
        for b in compile_bad:
            print("  -", b)
        return 1

    verify_status, verify_note = ("not-run", "--verify nahi diya")
    if verify:
        verify_status, verify_note = run_fix_tests(work)
        print(f"\nFix tests: {verify_status} - {verify_note}")

    bundle_dir = out / "bundle"
    if bundle_dir.exists():
        shutil.rmtree(bundle_dir)
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "repo_source": str(repo),
        "files": {},
    }
    for rel in changed:
        dst = bundle_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(work / rel, dst)
        manifest["files"][rel] = sha256_of((work / rel).read_bytes())
    manifest["verify"] = {"status": verify_status, "note": verify_note}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    zip_path = out / "bundle.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in changed:
            z.write(work / rel, arcname=rel)
        z.write(out / "manifest.json", arcname="manifest.json")

    write_report(out, results, manifest, verify_note, compile_bad)
    print(f"\nDone. {len(changed)} file(s) badli/nayi.")
    print(f"  bundle : {zip_path}")
    print(f"  repo   : {work}")
    print(f"  report : {out / 'PRODUCTION_FIXES.md'}")
    if verify_status == "FAILED":
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Strategy-Backtesting production fixes generator")
    ap.add_argument("--repo", required=True, type=Path, help="asli repo ka path")
    ap.add_argument("--out", type=Path, default=Path("fixes_out"), help="output folder")
    ap.add_argument("--verify", action="store_true", help="fix tests bhi chalao (pytest chahiye)")
    ap.add_argument("--dry-run", action="store_true", help="sirf dikhao, kuch mat likho")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s %(message)s")
    try:
        return build(args.repo.resolve(), args.out.resolve(), args.verify, args.dry_run)
    except SystemExit as e:
        log.error("%s", e)
        return 2


if __name__ == "__main__":
    sys.exit(main())
