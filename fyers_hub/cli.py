"""python -m fyers_hub <command>   (repo ke root se chalao)"""
from __future__ import annotations

import argparse
import csv
import shutil
import sys
import time
from datetime import date, timedelta

from fyers_hub import settings as cfg
from fyers_hub.settings import DEFAULT_BASE_TFS, DEFAULT_DERIVED_TFS, get_settings, read_symbol_file


def _api(s):
    from fyers_hub.client.api import FyersApi

    return FyersApi(s)


def _db(s):
    from fyers_hub.storage.db import connect

    return connect(s.db_path)


def _symbols(a, s):
    return a.symbols or read_symbol_file("watchlist.txt", s.home)


def cmd_init(a, s):
    s.home.mkdir(parents=True, exist_ok=True)
    for src, dst in ((cfg.PKG_DIR / "env.example", s.home / ".env"),
                     (cfg.PKG_DIR / "config" / "watchlist.txt", s.home / "watchlist.txt"),
                     (cfg.PKG_DIR / "config" / "underlyings.txt", s.home / "underlyings.txt")):
        if not dst.exists():
            shutil.copy(src, dst)
            print(f"bana: {dst}")
    (s.home / ".env").chmod(0o600)
    _db(s)
    print(f"Hub tayyar: {s.db_path}\nAb {s.home}/.env me FYERS_APP_ID aur FYERS_SECRET_KEY bharo.")


def cmd_doctor(a, s):
    from fyers_hub.auth.store import load_token

    print("python:", sys.version.split()[0])
    try:
        import fyers_apiv3  # noqa: F401
        print("fyers_apiv3: ok")
    except ImportError:
        print("fyers_apiv3: NAHI (pip install fyers-apiv3)")
    print("FYERS_APP_ID:", "set" if s.app_id else "KHALI")
    print("FYERS_SECRET_KEY:", "set" if s.secret_key else "KHALI")
    print("FYERS_PIN:", "set" if s.pin else "khali (auto-refresh band)")
    tok = load_token(s.token_path)
    print("token:", "valid" if tok and tok.valid() else "nahi / expire")
    print("db:", s.db_path, "(hai)" if s.db_path.exists() else "(nahi - init chalao)")


def cmd_auth_url(a, s):
    from fyers_hub.auth import flow

    print(flow.login_url(s))


def cmd_auth(a, s):
    from fyers_hub.auth import flow

    print("1) Ye link phone ke browser me kholo aur Fyers login karo:\n")
    print(flow.login_url(s))
    print("\n2) Login ke baad jo page khule uska POORA address (URL) copy karke yahan paste karo.")
    text = input("URL: ")
    tok = flow.exchange_code(flow.parse_auth_code(text, s), s)
    print(f"Token save ho gaya (~{int((tok.expires_at - time.time()) / 3600)} ghante). Dikhaya nahi jaata.")


def cmd_auth_code(a, s):
    from fyers_hub.auth import flow

    flow.exchange_code(flow.parse_auth_code(a.value, s), s)
    print("Token save ho gaya.")


def cmd_refresh(a, s):
    from fyers_hub.auth import flow

    flow.refresh(s)
    print("Token refresh ho gaya.")


def cmd_token_app(a, s):
    from fyers_hub.auth.web import serve

    serve(a.host, a.port)


def cmd_status(a, s):
    cmd_doctor(a, s)
    conn = _db(s)
    for t in ("instruments", "candles", "quotes", "option_chain"):
        print(f"{t}: {conn.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]} rows")
    try:
        p = _api(s).profile()
        print("Fyers login:", "ok" if p.get("s") == "ok" else p.get("message"))
    except Exception as e:  # noqa: BLE001
        print("Fyers login: fail -", e)


def cmd_symbols(a, s):
    from fyers_hub.ingest import instruments as ins

    conn = _db(s)
    for seg in a.segments:
        text = ins.download(seg)
        if a.inspect:
            for line in text.splitlines()[:3]:
                print(line)
            continue
        print(f"{seg}: {ins.load_into_db(conn, seg, text)} instruments")


def cmd_backfill(a, s):
    from fyers_hub.ingest.history import backfill

    end = date.today()
    tfs = a.tf or list(DEFAULT_BASE_TFS)
    conn, api = _db(s), _api(s)
    derive_tfs = [] if a.no_derive else (a.derive or list(DEFAULT_DERIVED_TFS))
    for sym_tf in tfs:
        days = a.days or (3650 if sym_tf.upper().endswith("D") else (25 if sym_tf.upper().endswith("S") else 400))
        backfill(api, conn, _symbols(a, s), [sym_tf], end - timedelta(days=days), end,
                 derive_tfs=derive_tfs if sym_tf in DEFAULT_BASE_TFS else ())


def cmd_derive(a, s):
    from fyers_hub.process.resample import derive

    conn = _db(s)
    for sym in _symbols(a, s):
        for t in a.to:
            print(f"{sym} {t}: {derive(conn, sym, t)} candles")


def cmd_chain(a, s):
    from fyers_hub.ingest.chain import snapshot_chain

    conn, api = _db(s), _api(s)
    for u in a.underlying or read_symbol_file("underlyings.txt", s.home):
        print(f"{u}: {snapshot_chain(api, conn, u, a.strikes, a.expiries, s.risk_free_rate)} rows")


def cmd_live(a, s):
    from fyers_hub.ingest.live import run_live

    run_live(_api(s), _db(s), _symbols(a, s), read_symbol_file("underlyings.txt", s.home),
             derive_tfs=DEFAULT_DERIVED_TFS, candle_symbols=a.candle_symbols, rate=s.risk_free_rate,
             chain_every=a.chain_every, n_expiries=a.expiries)


def cmd_ws(a, s):
    from fyers_hub.ingest.ws import run_ws

    run_ws(s, _symbols(a, s), tuple(a.tf))


def cmd_validate(a, s):
    from fyers_hub.process.quality import check_db

    conn = _db(s)
    for sym in _symbols(a, s):
        for tf in a.tf:
            r = check_db(conn, sym, tf)
            flag = "OK " if not (r["bad_ohlc"] or r["negative_volume"] or r["duplicates"] or r["short_days"]) else "!! "
            print(f"{flag}{sym} {tf}: rows={r['rows']} bad_ohlc={r['bad_ohlc']} short_days={len(r['short_days'])}")


def cmd_export(a, s):
    from fyers_hub.serve.hub import DataHub

    hub = DataHub(conn=_db(s))
    with open(a.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(("ts", "open", "high", "low", "close", "volume"))
        w.writerows(hub.candles(a.symbol, a.tf, a.start, a.end))
    print("saved:", a.out)


def cmd_prune(a, s):
    from fyers_hub.ingest.chain import prune_chain

    print("deleted rows:", prune_chain(_db(s), a.days))


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="fyers_hub")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add(name, fn, **kw):
        sp = sub.add_parser(name, **kw)
        sp.set_defaults(fn=fn)
        return sp

    add("init", cmd_init, help="folder, .env, watchlist, db banao")
    add("doctor", cmd_doctor, help="setup check")
    add("auth-url", cmd_auth_url, help="Fyers login link")
    add("auth", cmd_auth, help="login link -> URL paste -> token save")
    sp = add("auth-code", cmd_auth_code, help="redirect URL ya auth_code se token")
    sp.add_argument("value")
    add("refresh", cmd_refresh, help="PIN se token refresh")
    sp = add("token-app", cmd_token_app, help="browser token app")
    sp.add_argument("--host", default="127.0.0.1")
    sp.add_argument("--port", type=int, default=8765)
    add("status", cmd_status, help="token + hub + Fyers login")
    sp = add("symbols", cmd_symbols, help="symbol master download")
    sp.add_argument("--segments", nargs="+", default=["NSE_CM", "NSE_FO"])
    sp.add_argument("--inspect", action="store_true", help="CSV ki pehli 3 lines dikhao")
    sp = add("backfill", cmd_backfill, help="purani candles khincho")
    sp.add_argument("--symbols", nargs="+")
    sp.add_argument("--tf", nargs="+", help="jaise 1 D 5S (default: 1 D)")
    sp.add_argument("--days", type=int)
    sp.add_argument("--derive", nargs="+")
    sp.add_argument("--no-derive", action="store_true")
    sp = add("derive", cmd_derive, help="hub ki candles se naya timeframe banao")
    sp.add_argument("--symbols", nargs="+")
    sp.add_argument("--to", nargs="+", required=True)
    sp = add("chain", cmd_chain, help="option chain + greeks snapshot")
    sp.add_argument("--underlying", nargs="+")
    sp.add_argument("--strikes", type=int, default=10)
    sp.add_argument("--expiries", type=int, default=2)
    sp = add("live", cmd_live, help="live loop (bhav + chain + candles)")
    sp.add_argument("--symbols", nargs="+")
    sp.add_argument("--candle-symbols", nargs="+")
    sp.add_argument("--chain-every", type=int, default=60)
    sp.add_argument("--expiries", type=int, default=2)
    sp = add("ws", cmd_ws, help="websocket se live 5S/1m candles")
    sp.add_argument("--symbols", nargs="+")
    sp.add_argument("--tf", nargs="+", default=["5S", "1"])
    sp = add("validate", cmd_validate, help="data quality check")
    sp.add_argument("--symbols", nargs="+")
    sp.add_argument("--tf", nargs="+", default=["1", "D"])
    sp = add("export", cmd_export, help="candles CSV me")
    sp.add_argument("symbol")
    sp.add_argument("tf")
    sp.add_argument("--start")
    sp.add_argument("--end")
    sp.add_argument("--out", default="candles.csv")
    sp = add("prune", cmd_prune, help="purani option chain snapshots hatao")
    sp.add_argument("--days", type=int, default=30)

    a = p.parse_args(argv)
    try:
        a.fn(a, get_settings())
    except KeyboardInterrupt:
        return 130
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    return 0
