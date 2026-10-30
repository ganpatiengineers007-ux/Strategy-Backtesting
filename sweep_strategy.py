"""
FILE   : sweep_strategy.py
STATUS : COMPLETE (पूरी चलने लायक फ़ाइल — कोई placeholder नहीं)
PATH   : ./sweep_strategy.py  (अपने प्रोजेक्ट फ़ोल्डर के रूट में रखें)

BANKNIFTY/NIFTY Futures — Liquidity Sweep & Stop-Hunting Reversal
=================================================================
HFT-style, tick-driven strategy on DhanHQ v2 (pip install dhanhq, v2.3.x).
Indicator-free by design: price action + volume rate + order-book depth.
No RSI/MACD/Stochastic — none, ever.

Idea: retail stop-losses cluster just beyond obvious levels (previous-day
high/low, classic pivots, round numbers, session high/low). A "stop hunt"
pokes through the level, absorbs those stops, then price RECLAIMS the level.
We buy the reclaim (mirror-sell the upside sweep), with depth confirmation.

High-frequency elements (within retail-API reality):
  * Pure event loop — every tick drives decisions, no polling delays.
  * O(1) incremental state: rolling volume-rate via a small deque.
  * 200-level FullDepth imbalance check at the reclaim moment (auto-fallback
    if depth feed is unavailable).
  * Kill-switch: daily loss cap + max trades; journal of every trade.

Honest limits: DhanHQ WebSocket gives ~1-5 updates/sec on index futures, no
colocation. This is HFT-STYLE architecture, not co-located HFT.

Credentials (env vars, never hardcode):
    export DHAN_CLIENT_ID=...
    export DHAN_ACCESS_TOKEN=...
NOTE: SECURITY_ID must be the CURRENT-month contract id (verify per expiry).
"""

import os
import csv
import sys
import time
import logging
import threading
from collections import deque
from datetime import datetime, time as dtime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd

from dhanhq import DhanContext, dhanhq, MarketFeed

try:
    from dhanhq import FullDepth
    HAVE_DEPTH = True
except ImportError:
    HAVE_DEPTH = False

# ------------------------------------------------------------------ config
IST = ZoneInfo("Asia/Kolkata")

SECURITY_ID      = "49081"        # NIFTY current-month futures (VERIFY per expiry)
EXCHANGE_SEGMENT = MarketFeed.NSE_FNO
LOT_SIZE         = 65             # NIFTY: 65 from Jan-2026 series (NSE FAOP70616); BANKNIFTY: 30
MAX_LOTS         = 4
RISK_PER_TRADE   = 2000           # ₹ risk per trade (~1% of a ₹2L account)
CAPITAL          = 200000         # for the 1%-risk rule check
RISK_SKIP_X      = 1.5            # skip trade if 1 lot risks > 1.5x RISK_PER_TRADE

# --- sweep detection (all price-action / volume — no indicators)
SWEEP_POKE_MAX   = 0.0015         # poke beyond level must be < 0.15% of price
RECLAIM_GRACE_SEC= 180            # reclaim must happen within 3 minutes
VOL_RATE_X       = 2.0            # sweep-period volume rate >= 2x session avg
VOL_WINDOW_SEC   = 120            # rolling window for volume rate
DEPTH_IMB_MIN    = 1.5            # bid:ask qty ratio at reclaim (depth confirm)
USE_DEPTH        = True           # needs FullDepth feed; auto-falls back
ALLOW_SHORT      = True
ROUND_STEP       = 100            # round-number clusters (NIFTY: 100s)

# --- exits & risk
ATR_LEN          = 14             # ATR only sizes the stop (allowed tool)
STOP_ATR_MULT    = 0.25
BREAKEVEN_AT_R   = 1.0
TRAIL_ATR_MULT   = 2.5            # chandelier trail after breakeven
TIME_STOP_SEC    = 45 * 60        # exit stale trades after 45 min
MAX_TRADES_DAY   = 3
DAILY_LOSS_CAP   = 4000

ENTRY_START   = dtime(9, 30)
LAST_ENTRY    = dtime(14, 30)
SQUARE_OFF    = dtime(15, 20)

DRY_RUN   = True
TRADE_LOG = "sweep_trades.csv"
TAG       = "sweep"

log = logging.getLogger("sweep")

# ------------------------------------------------------------------ helpers
def now_ist() -> datetime:
    return datetime.now(IST)

def fmt(x: float) -> str:
    return f"{x:,.2f}"

def compute_atr(df: pd.DataFrame, n: int = 14) -> float:
    h, l, c = df["high"], df["low"], df["close"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return float(tr.ewm(alpha=1 / n, adjust=False).mean().iloc[-1]) or 0.0

def classic_pivots(prev_h: float, prev_l: float, prev_c: float) -> dict:
    pp = (prev_h + prev_l + prev_c) / 3.0
    return {"PP": pp, "R1": 2 * pp - prev_l, "S1": 2 * pp - prev_h}

def round_levels(price: float, step: float, n_each: int = 2) -> list[float]:
    base = int(price // step) * step
    return [base + i * step for i in range(-n_each, n_each + 1)]

# ------------------------------------------------------------------ candle builder
class CandleBuilder:
    """5-minute OHLCV candles built from ticks; volume taken as day-cumulative delta."""

    def __init__(self, sec: int):
        self.sec = sec
        self.cur = None
        self.last_cum_vol = 0.0
        self.closed = None

    def add(self, price: float, cum_volume: float):
        ts = now_ist()
        bucket = int(ts.timestamp() // self.sec) * self.sec
        self.closed = None
        if self.cur is None or bucket > self.cur["bucket"]:
            if self.cur is not None:
                self.closed = self.cur
                self.last_cum_vol = self.cur["cum_vol_end"]
            self.cur = {
                "bucket": bucket, "ts": ts,
                "open": price, "high": price, "low": price, "close": price,
                "volume": max(0.0, cum_volume - self.last_cum_vol),
                "cum_vol_end": cum_volume,
            }
        else:
            c = self.cur
            c["high"] = max(c["high"], price)
            c["low"] = min(c["low"], price)
            c["close"] = price
            c["cum_vol_end"] = cum_volume
            c["volume"] = max(c["volume"], cum_volume - self.last_cum_vol)

    def pop_closed(self):
        c = self.closed
        self.closed = None
        return c

# ------------------------------------------------------------------ depth reader
class DepthReader:
    """200-level order book -> single imbalance ratio near the touch.
    Degrades to ratio 1.0 (neutral) if the feed or packet shape differs."""

    def __init__(self):
        self.ratio = 1.0
        self.live = False        # True only after the first REAL depth packet
        self.last_pkt = None

    def update(self, pkt) -> None:
        if not isinstance(pkt, dict):
            return
        self.live = True
        if self.last_pkt is None:
            log.debug(f"first depth packet — verify keys: {str(pkt)[:300]}")
        self.last_pkt = 1
        bids = pkt.get("bids") or pkt.get("buy") or pkt.get("bidDetails") or []
        asks = pkt.get("asks") or pkt.get("sell") or pkt.get("askDetails") or []

        def total(levels):
            tot = 0.0
            for lv in levels[:20]:
                if isinstance(lv, dict):
                    tot += float(lv.get("quantity") or lv.get("size") or lv.get("qty") or 0)
            return tot

        b, a = total(bids), total(asks)
        if a > 0:
            self.ratio = b / a

    def imbalance(self, side: str) -> float:
        """For LONG entries we want bids absorbing (ratio>1);
        for SHORT entries we want asks absorbing (ratio<1)."""
        return self.ratio if side == "LONG" else (1.0 / self.ratio if self.ratio > 0 else 0.0)

# ------------------------------------------------------------------ journal
def journal_trade(side, qty, entry, exit_price, reason, pnl):
    new = not os.path.exists(TRADE_LOG)
    with open(TRADE_LOG, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["date", "time", "side", "qty", "entry", "exit", "reason", "pnl"])
        w.writerow([now_ist().date().isoformat(), now_ist().strftime("%H:%M:%S"),
                    side, qty, f"{entry:.2f}", f"{exit_price:.2f}", reason, f"{pnl:.2f}"])

# ------------------------------------------------------------------ strategy
class SweepStrategy:
    def __init__(self, api: dhanhq, depth: DepthReader):
        self.api = api
        self.depth = depth
        self.position = None
        self.trades_today = 0
        self.realized_pnl = 0.0
        self.halted = False
        self.candles: list[dict] = []
        # liquidity levels: [{"name","price","kind"}] — support/resistance
        self.levels: list[dict] = []
        self.session_high = None
        self.session_low = None
        # active sweep watch: {"side","level","extreme","ts"}
        self.sweep = None
        # volume-rate state (O(1) rolling)
        self.vol_samples = deque(maxlen=600)   # (epoch_sec, cum_vol)
        self.cum_vol = 0.0
        self.start_epoch = None
        self.atr = 0.0

    # ---------------- setup
    def build_levels(self, ltp: float):
        """Round numbers always; prev-day H/L + classic pivots when history
        is reachable (any failure just skips those levels gracefully)."""
        for p in round_levels(ltp, ROUND_STEP):
            self.levels.append({"name": f"R{p:.0f}", "price": float(p), "kind": "both"})
        try:
            to_ = now_ist().date()
            from_ = to_ - timedelta(days=7)
            resp = self.api.historical_daily_data(
                security_id=SECURITY_ID, exchange_segment="NSE_FNO",
                instrument_type="FUTIDX", from_date=from_.isoformat(),
                to_date=(to_ - timedelta(days=1)).isoformat(),
            )
            rows = resp.get("data") if isinstance(resp, dict) else resp
            if isinstance(rows, list) and rows:
                day = rows[-1]
                h, l, c = float(day["high"]), float(day["low"]), float(day["close"])
                piv = classic_pivots(h, l, c)
                self.levels += [
                    {"name": "PDH", "price": h, "kind": "resistance"},
                    {"name": "PDL", "price": l, "kind": "support"},
                    {"name": "R1", "price": piv["R1"], "kind": "resistance"},
                    {"name": "PP", "price": piv["PP"], "kind": "both"},
                    {"name": "S1", "price": piv["S1"], "kind": "support"},
                ]
                log.info(f"levels: PDH {fmt(h)} PDL {fmt(l)} PP {fmt(piv['PP'])}")
        except Exception as e:                                       # noqa: BLE001
            log.warning(f"prev-day levels unavailable ({type(e).__name__}) — round numbers only")

    # ---------------- orders
    def _order(self, side: str, qty: int, why: str) -> str:
        if DRY_RUN:
            log.info(f"[DRY-RUN] {side} {qty} @ mkt · {why}")
            return f"DRY-{side}"
        try:
            resp = self.api.place_order(
                security_id=SECURITY_ID, exchange_segment="NSE_FNO",
                transaction_type=side, quantity=qty, order_type="MARKET",
                product_type="INTRADAY", validity="DAY", price=0,
                tag=f"{TAG}-{why[:12]}",
            )
            oid = resp.get("orderId") if isinstance(resp, dict) else resp
            log.info(f"order {oid} accepted · {side} {qty} · {why}")
            return oid
        except Exception as e:                                       # noqa: BLE001
            log.error(f"order failed ({side} {qty}): {e}")
            return ""

    def _enter(self, side: str, entry: float, stop: float, level_name: str):
        risk_pts = abs(entry - stop)
        if risk_pts <= 0:
            return
        # GUARD (नया): अगर 1 लॉट का रिस्क ही सीमा से ज़्यादा है तो ट्रेड छोड़ दो
        if risk_pts * LOT_SIZE > RISK_SKIP_X * RISK_PER_TRADE:
            log.info(f"skip · 1-lot risk ₹{fmt(risk_pts * LOT_SIZE)} > "
                     f"{RISK_SKIP_X}x limit ₹{fmt(RISK_PER_TRADE)}")
            return
        lots = max(1, min(MAX_LOTS, int(RISK_PER_TRADE // (risk_pts * LOT_SIZE))))
        qty = lots * LOT_SIZE
        self._order("BUY" if side == "LONG" else "SELL", qty, f"entry-{level_name}")
        self.position = {
            "side": side, "entry": entry, "stop": stop, "qty": qty,
            "risk_pts": risk_pts, "be_moved": False,
            "best": entry, "entry_ts": now_ist(),
        }
        self.trades_today += 1
        log.info(f"{side} {qty} @ ~{fmt(entry)} · stop {fmt(stop)} "
                 f"({fmt(risk_pts)} pts, ₹{fmt(risk_pts * qty)} risk) · {level_name}")

    def _exit(self, price: float, why: str):
        p = self.position
        self._order("SELL" if p["side"] == "LONG" else "BUY", p["qty"], why)
        pnl = (price - p["entry"]) * p["qty"] if p["side"] == "LONG" \
            else (p["entry"] - price) * p["qty"]
        self.realized_pnl += pnl
        log.info(f"EXIT {why} @ ~{fmt(price)} · PnL ₹{fmt(pnl)} · day ₹{fmt(self.realized_pnl)}")
        journal_trade(p["side"], p["qty"], p["entry"], price, why, pnl)
        self.position = None
        if self.realized_pnl <= -DAILY_LOSS_CAP:
            log.warning(f"KILL-SWITCH: daily loss ₹{fmt(self.realized_pnl)} — halting")
            self.halted = True

    # ---------------- tick engine (the whole strategy lives here)
    def on_tick(self, ltp: float, cum_vol: float):
        ts = now_ist()
        ep = ts.timestamp()
        if self.start_epoch is None:
            self.start_epoch = ep
        self.cum_vol = cum_vol
        self.vol_samples.append((ep, cum_vol))

        # session extremes
        if self.session_high is None:
            self.session_high = self.session_low = ltp
        self.session_high = max(self.session_high, ltp)
        self.session_low = min(self.session_low, ltp)

        if self.position is not None:
            self._manage(ltp, ts)
            return
        if self.halted or not (ENTRY_START <= ts.time() <= LAST_ENTRY):
            return
        if self.trades_today >= MAX_TRADES_DAY:
            return
        if self.atr <= 0:
            return   # WARM-UP: ATR (and the session volume baseline) not
                     # reliable yet — no entries until ~5 candles are closed.
                     # Also prevents the stop from being placed with a zero
                     # ATR buffer (too tight -> excess stop-outs).

        # 1) poke detection: tick crosses below a support (or above resistance)
        if self.sweep is None:
            for lv in self.levels:
                kind = lv["kind"]
                if kind in ("support", "both") and ltp < lv["price"] <= ltp * (1 + SWEEP_POKE_MAX):
                    self.sweep = {"side": "LONG", "level": lv, "extreme": ltp, "ts": ts}
                    log.debug(f"sweep watch · poked below {lv['name']} {fmt(lv['price'])}")
                    break
                if ALLOW_SHORT and kind in ("resistance", "both") \
                        and ltp > lv["price"] >= ltp * (1 - SWEEP_POKE_MAX):
                    self.sweep = {"side": "SHORT", "level": lv, "extreme": ltp, "ts": ts}
                    log.debug(f"sweep watch · poked above {lv['name']} {fmt(lv['price'])}")
                    break
            return

        # 2) grace period: track the extreme, then wait for the reclaim tick
        if (ts - self.sweep["ts"]).total_seconds() > RECLAIM_GRACE_SEC:
            self.sweep = None                       # failed hunt — reset, no trade
            return
        s = self.sweep
        if s["side"] == "LONG":
            s["extreme"] = min(s["extreme"], ltp)
            if ltp > s["level"]["price"]:           # RECLAIM!
                if self._confirmed(s, "LONG"):
                    stop = s["extreme"] - STOP_ATR_MULT * self.atr
                    log.info(f"SIGNAL LONG · stop-hunt reclaim of {s['level']['name']}")
                    self._enter("LONG", ltp, stop, s["level"]["name"])
                self.sweep = None
        else:
            s["extreme"] = max(s["extreme"], ltp)
            if ltp < s["level"]["price"]:
                if self._confirmed(s, "SHORT"):
                    stop = s["extreme"] + STOP_ATR_MULT * self.atr
                    log.info(f"SIGNAL SHORT · stop-hunt reclaim of {s['level']['name']}")
                    self._enter("SHORT", ltp, stop, s["level"]["name"])
                self.sweep = None

    def _confirmed(self, s: dict, side: str) -> bool:
        """Volume-rate spike during the sweep + depth imbalance at reclaim.
        The depth check applies ONLY when the depth feed is actually LIVE —
        a dead/silent feed must never silently block every signal."""
        ok_vol = self._vol_rate_spike()
        ok_depth = True
        if USE_DEPTH and HAVE_DEPTH and self.depth.live:
            ok_depth = self.depth.imbalance(side) >= DEPTH_IMB_MIN
            if not ok_depth:
                log.debug(f"depth ratio {self.depth.imbalance(side):.2f} < {DEPTH_IMB_MIN} — skip")
        return ok_vol and ok_depth

    def _vol_rate_spike(self) -> bool:
        if len(self.vol_samples) < 2:
            return False
        now_ep, now_v = self.vol_samples[-1]
        then_ep = now_ep - VOL_WINDOW_SEC
        base_v = None
        for ep, v in self.vol_samples:
            if ep >= then_ep:
                base_v = v
                break
        if base_v is None or now_ep - then_ep <= 0:
            return False
        window_rate = max(0.0, now_v - base_v) / VOL_WINDOW_SEC
        elapsed = max(1.0, now_ep - self.start_epoch)
        avg_rate = max(0.0, self.cum_vol) / elapsed
        if avg_rate <= 0:
            return False
        spike = window_rate >= VOL_RATE_X * avg_rate
        if not spike:
            log.debug(f"vol-rate {window_rate:.0f}/s vs avg {avg_rate:.0f}/s — no spike")
        return spike

    # ---------------- position management (tick-level)
    def _manage(self, ltp: float, ts: datetime):
        p = self.position
        long = p["side"] == "LONG"
        r_move = (ltp - p["entry"]) if long else (p["entry"] - ltp)
        p["best"] = max(p["best"], ltp) if long else min(p["best"], ltp)
        # breakeven
        if not p["be_moved"] and r_move >= BREAKEVEN_AT_R * p["risk_pts"]:
            p["stop"] = p["entry"] + (2.0 if long else -2.0)
            p["be_moved"] = True
            log.info(f"trail stop -> breakeven @ {fmt(p['stop'])}")
        # chandelier trail after breakeven
        if p["be_moved"] and self.atr > 0:
            trail = (p["best"] - TRAIL_ATR_MULT * self.atr) if long \
                else (p["best"] + TRAIL_ATR_MULT * self.atr)
            p["stop"] = max(p["stop"], trail) if long else min(p["stop"], trail)
        # time stop
        if (ts - p["entry_ts"]).total_seconds() >= TIME_STOP_SEC:
            self._exit(ltp, "time-stop")
            return
        hit_stop = ltp <= p["stop"] if long else ltp >= p["stop"]
        if hit_stop:
            self._exit(ltp, "stop-loss" if not p["be_moved"] else "trail-exit")

    def on_candle(self, candle: dict):
        """Candles are used ONLY for ATR (stop sizing) — decisions are tick-driven."""
        self.candles.append(candle)
        if len(self.candles) >= 5:
            self.atr = compute_atr(pd.DataFrame(self.candles), ATR_LEN)

    def square_off(self, ltp: float):
        if self.position is not None:
            self._exit(ltp, "eod-square-off")

    def day_summary(self):
        log.info(f"day summary · trades {self.trades_today} · realized ₹{fmt(self.realized_pnl)}")

# ------------------------------------------------------------------ wiring
def parse_tick(msg: dict):
    ltp = (msg.get("LTP") or msg.get("ltp") or msg.get("last_price") or msg.get("lp")
           or (msg.get("ohlc") or {}).get("close"))
    vol = msg.get("volume") or msg.get("Volume") or msg.get("ttq") or msg.get("v") or 0
    return ltp, float(vol)

def depth_worker(depth_feed, depth: DepthReader):
    """Depth feed को अलग thread में पढ़ो ताकि यह मुख्य tick loop को ब्लॉक न करे."""
    while True:
        try:
            pkt = depth_feed.get_data()
            if pkt is not None:
                depth.update(pkt)
        except Exception as e:                                       # noqa: BLE001
            log.warning(f"depth read error ({type(e).__name__}) — retry in 2s")
            time.sleep(2)

def main():
    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s.%(msecs)03d  %(levelname)-5s  %(message)s",
                        datefmt="%H:%M:%S")
    client_id = os.environ.get("DHAN_CLIENT_ID", "")
    token = os.environ.get("DHAN_ACCESS_TOKEN", "")
    if not client_id or not token:
        log.error("set DHAN_CLIENT_ID and DHAN_ACCESS_TOKEN env vars")
        sys.exit(1)

    ctx = DhanContext(client_id, token)
    api = dhanhq(ctx)
    depth = DepthReader()
    strat = SweepStrategy(api, depth)
    builder = CandleBuilder(300)

    feed = MarketFeed(ctx, [(EXCHANGE_SEGMENT, SECURITY_ID, MarketFeed.Quote)], version="v2")
    feed.run_forever()

    depth_feed = None
    if USE_DEPTH and HAVE_DEPTH:
        try:
            depth_feed = FullDepth(ctx, [(int(EXCHANGE_SEGMENT), SECURITY_ID)], 200)
            depth_feed.run_forever()
            threading.Thread(target=depth_worker, args=(depth_feed, depth),
                             daemon=True).start()
            log.info("depth feed started · 200-level (live only after first packet)")
        except Exception as e:                                       # noqa: BLE001
            log.warning(f"depth feed unavailable ({type(e).__name__}) — continuing without")
    log.info(f"subscribed {SECURITY_ID} · tick-driven · feed ok · DRY_RUN={DRY_RUN}")

    state = {"first": False, "last_ltp": None, "last_vol": 0.0, "flattened": False}

    def handle(msg: dict):
        ltp, cum_vol = parse_tick(msg)
        if ltp is None:
            return
        ltp = float(ltp)
        if cum_vol <= 0:                 # ticker-type packet में volume नहीं होता
            cum_vol = state["last_vol"]
        else:
            state["last_vol"] = cum_vol
        state["last_ltp"] = ltp
        if not state["first"]:
            state["first"] = True
            strat.build_levels(ltp)
            log.debug(f"first raw tick packet — verify keys: {msg}")
        builder.add(ltp, cum_vol)
        closed = builder.pop_closed()
        if closed is not None:
            strat.on_candle(closed)
        strat.on_tick(ltp, cum_vol)

    try:
        while True:
            try:
                msg = feed.get_data()
            except Exception as e:                                   # noqa: BLE001
                log.warning(f"feed error ({type(e).__name__}: {e}) — retry in 2s")
                time.sleep(2)
                continue
            if isinstance(msg, dict):
                handle(msg)

            if now_ist().time() >= SQUARE_OFF and not state["flattened"]:
                state["flattened"] = True
                if state["last_ltp"] is not None:
                    strat.square_off(state["last_ltp"])
                strat.day_summary()
                break
    except KeyboardInterrupt:
        log.warning("Ctrl-C — flattening and exiting")
        if state["last_ltp"] is not None:
            strat.square_off(state["last_ltp"])
        strat.day_summary()
    finally:
        try:
            feed.disconnect()
        except Exception:                                            # noqa: BLE001
            pass

if __name__ == "__main__":
    main()
