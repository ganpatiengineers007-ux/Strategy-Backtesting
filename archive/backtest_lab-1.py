"""
backtest_lab.py  -  NSE ke liye global strategies ka BACKTEST-ONLY lab
(GTS se alag. Koi live order nahi, koi broker connection nahi.)

Chalane ke liye:   python backtest_lab.py

Isme 5 module hain:
  1. Pairs / Stat Arb          (US/Japan se)
  2. Reversal + Turnover       (China A-share se)
  3. VWAP / TWAP execution     (Europe/APAC se)
  4. Iceberg / Order-flow      (tick data par)
  5. Market-making simulation  (US/Japan se, sirf simulation)

DHYAN: abhi data SYNTHETIC (nakli) hai taaki code test ho sake.
Synthetic par achha result aana koi saboot nahi hai. Asli data ke liye
neeche load_daily_csv() / load_tick_csv() use karein.
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = "lab_reports"
COST_BPS = 5.0          # har taraf ki lagat (brokerage+STT+slippage ka andaza)
os.makedirs(OUT, exist_ok=True)


# =====================================================================
# Common: metrics aur data loaders
# =====================================================================
def metrics(ret, periods=252):
    ret = ret.dropna()
    if len(ret) < 2 or ret.std() == 0:
        return {"CAGR%": 0.0, "Sharpe": 0.0, "MaxDD%": 0.0, "Din": len(ret)}
    eq = (1 + ret).cumprod()
    years = len(ret) / periods
    cagr = eq.iloc[-1] ** (1 / years) - 1
    sharpe = ret.mean() / ret.std() * np.sqrt(periods)
    dd = (eq / eq.cummax() - 1).min()
    return {"CAGR%": round(float(cagr) * 100, 2), "Sharpe": round(float(sharpe), 2),
            "MaxDD%": round(float(dd) * 100, 2), "Din": len(ret)}


def load_daily_csv(path):
    """CSV columns: date, symbol, close, volume  ->  (close, volume) pivot"""
    df = pd.read_csv(path, parse_dates=["date"])
    close = df.pivot(index="date", columns="symbol", values="close").sort_index()
    vol = df.pivot(index="date", columns="symbol", values="volume").sort_index()
    return close, vol


def load_tick_csv(path):
    """CSV columns: timestamp, price, size, side(+1 buy / -1 sell)"""
    return pd.read_csv(path, parse_dates=["timestamp"])


def save_equity_chart(curves, title, fname):
    plt.figure(figsize=(10, 5))
    for name, r in curves.items():
        plt.plot((1 + r.fillna(0)).cumprod(), label=name)
    plt.title(title)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, fname), dpi=150)
    plt.close()


# =====================================================================
# 1. PAIRS / STAT ARB
# =====================================================================
def synthetic_pair(n=1500, seed=1):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2020-01-01", periods=n)
    common = np.cumsum(rng.normal(0.0003, 0.01, n))
    spread = np.zeros(n)
    for i in range(1, n):
        spread[i] = 0.95 * spread[i - 1] + rng.normal(0, 0.006)
    a = 100 * np.exp(common)
    b = 200 * np.exp(1.1 * common + spread)
    return pd.DataFrame({"A": a, "B": b}, index=idx)


def pairs_backtest(px, a="A", b="B", win=60, train=250, entry=2.0,
                   exit_=0.5, cost_bps=COST_BPS):
    la, lb = np.log(px[a]), np.log(px[b])
    # beta sirf shuru ke 'train' din se nikalo, phir fix rakho (out-of-sample)
    beta_val = np.cov(la.iloc[:train], lb.iloc[:train])[0, 1] / np.var(lb.iloc[:train], ddof=1)
    beta = pd.Series(beta_val, index=px.index)
    spread = la - beta * lb
    z = (spread - spread.rolling(win).mean()) / spread.rolling(win).std()

    pos = np.zeros(len(z))
    cur = 0
    for i, zi in enumerate(z.values):
        if np.isnan(zi):
            pos[i] = 0
            continue
        if cur == 0:
            if zi > entry:
                cur = -1
            elif zi < -entry:
                cur = 1
        elif cur == 1 and zi > -exit_:
            cur = 0
        elif cur == -1 and zi < exit_:
            cur = 0
        pos[i] = cur
    pos[:train] = 0                                           # training me trade nahi
    pos = pd.Series(pos, index=px.index).shift(1).fillna(0)   # agle din execute

    ra, rb = px[a].pct_change(), px[b].pct_change()
    bprev = beta.shift(1)
    gross = 1 + bprev.abs()
    pnl = pos * (ra - bprev * rb) / gross
    cost = pos.diff().abs().fillna(0) * (cost_bps / 1e4) * 2
    net = (pnl - cost).fillna(0)
    return net, pos


# =====================================================================
# 2. REVERSAL + TURNOVER (China A-share idea)
# =====================================================================
def synthetic_universe(n_days=1000, n_stocks=60, seed=2):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2021-01-01", periods=n_days)
    cols = [f"S{i:02d}" for i in range(n_stocks)]
    mkt = rng.normal(0.0004, 0.008, (n_days, 1))
    ret = mkt + rng.normal(0, 0.015, (n_days, n_stocks))
    for t in range(1, n_days):
        ret[t] -= 0.05 * ret[t - 1]          # halka mean-reversion (nakli)
    close = pd.DataFrame(100 * np.cumprod(1 + ret, axis=0), idx, cols)
    vol = pd.DataFrame(rng.lognormal(12, 0.4, (n_days, n_stocks)) *
                       (1 + 5 * np.abs(ret)), idx, cols)
    return close, vol


def reversal_turnover_backtest(close, vol, lookback=5, rebal=5, q=0.2,
                               w_turn=0.5, cost_bps=COST_BPS):
    ret = close.pct_change()
    rev = -close.pct_change(lookback)                       # haare hue upar
    rel_turn = (vol / vol.rolling(60).mean()).rolling(lookback).mean()
    score = (rev.rank(axis=1, pct=True)
             + w_turn * (-rel_turn).rank(axis=1, pct=True))  # kam turnover upar

    w = pd.DataFrame(np.nan, index=close.index, columns=close.columns)
    for i in range(70, len(close), rebal):
        s = score.iloc[i].dropna()
        if len(s) < 5:
            continue
        n = max(1, int(len(s) * q))
        row = pd.Series(0.0, index=close.columns)
        row[s.nlargest(n).index] = 1.0 / n
        row[s.nsmallest(n).index] = -1.0 / n
        w.iloc[i] = row
    w = w.ffill().fillna(0).shift(1)
    pnl = (w * ret).sum(axis=1)
    cost = w.diff().abs().sum(axis=1) * (cost_bps / 1e4)
    return (pnl - cost).fillna(0)


# =====================================================================
# 3. VWAP / TWAP EXECUTION SIMULATION
# =====================================================================
def execution_sim(n_sims=300, parent_qty=100000, n_bars=75, seed=3):
    """5-minute bars (9:15-15:30). BUY order ko 3 tareeke se bharte hain."""
    rng = np.random.default_rng(seed)
    u = np.linspace(-1, 1, n_bars)
    profile = 1 + 1.5 * u ** 2                     # U-shape volume
    profile = profile / profile.sum()
    schedules = {
        "Aggressive (1 bar)": np.r_[parent_qty, np.zeros(n_bars - 1)],
        "TWAP": np.full(n_bars, parent_qty / n_bars),
        "VWAP": profile * parent_qty,
    }
    rows = {k: [] for k in schedules}
    for _ in range(n_sims):
        price = 100 * np.exp(np.cumsum(rng.normal(0, 0.0007, n_bars)))
        mkt_vol = profile * rng.uniform(4e6, 6e6) * rng.lognormal(0, 0.1, n_bars)
        arrival = price[0]
        mkt_vwap = (price * mkt_vol).sum() / mkt_vol.sum()
        for name, q in schedules.items():
            part = q / mkt_vol
            fill = price * (1 + 30 * np.sqrt(part) / 1e4)   # sqrt impact model
            avg = (fill * q).sum() / q.sum()
            rows[name].append(((avg / arrival - 1) * 1e4,
                               (avg / mkt_vwap - 1) * 1e4))
    out = []
    for name, v in rows.items():
        v = np.array(v)
        out.append({"Tareeka": name,
                    "Slippage vs Arrival (bps)": round(v[:, 0].mean(), 2),
                    "Slippage vs VWAP (bps)": round(v[:, 1].mean(), 2),
                    "Std (bps)": round(v[:, 0].std(), 2)})
    return pd.DataFrame(out)


# =====================================================================
# 4. ICEBERG / ORDER-FLOW (tick data)
# =====================================================================
def synthetic_ticks(n=20000, seed=4, tick=0.05):
    rng = np.random.default_rng(seed)
    ts = pd.date_range("2026-10-30 09:15:00", periods=n, freq="250ms")
    price = 100 + np.cumsum(rng.normal(0, 0.03, n))
    size = rng.choice([100, 500, 2000], size=n, p=[0.6, 0.3, 0.1]).astype(float)
    side = rng.choice([1, -1], size=n)

    def inject(start, end, direction, drift):
        lvl = price[start]
        mask = rng.random(end - start) < 0.7
        idxs = np.arange(start, end)[mask]
        price[idxs] = lvl
        size[idxs] = rng.choice([100, 150, 200, 250], size=len(idxs))
        side[idxs] = direction
        price[end:] += drift                      # chhupe order ke baad chaal

    # drift ko shor (~0.67 per 500 tick) se bada rakha hai, warna test bematlab
    inject(5000, 5400, +1, +1.50)                 # chhupa kharidar
    inject(12000, 12400, -1, -1.50)               # chhupa becchne wala
    price = np.round(price / tick) * tick
    return pd.DataFrame({"timestamp": ts, "price": price,
                         "size": size, "side": side})


def detect_iceberg(df, win=50, min_trades=20, min_vol=4000,
                   max_avg_size=400, dir_ratio=0.7, tick=0.05):
    lvl = (df["price"] / tick).round().astype(int).values
    size = df["size"].values
    side = df["side"].values
    n = len(df)
    cnt = np.zeros(n)
    vol = np.zeros(n)
    net = np.zeros(n)
    for i in range(n):
        s = max(0, i - win + 1)
        m = lvl[s:i + 1] == lvl[i]
        cnt[i] = m.sum()
        vol[i] = size[s:i + 1][m].sum()
        net[i] = (size[s:i + 1] * side[s:i + 1])[m].sum()
    avg = np.divide(vol, cnt, out=np.zeros(n), where=cnt > 0)
    sig = ((cnt >= min_trades) & (vol >= min_vol) & (avg <= max_avg_size)
           & (np.abs(net) >= dir_ratio * vol))
    out = df.copy()
    out["iceberg"] = sig
    out["dir"] = np.sign(net) * sig
    return out


def merge_zones(d, gap=100, min_volume=5000):
    idx = np.where(d["iceberg"].values)[0]
    if len(idx) == 0:
        return pd.DataFrame(columns=["start", "end", "price", "dir", "volume"])
    zones, s, p = [], idx[0], idx[0]
    for i in idx[1:]:
        if i - p > gap:
            zones.append((s, p))
            s = i
        p = i
    zones.append((s, p))
    rows = []
    for a, b in zones:
        seg = d.iloc[a:b + 1]
        rows.append({"start": a, "end": b, "price": round(seg["price"].median(), 2),
                     "dir": int(np.sign(seg["dir"].sum())),
                     "volume": float(seg["size"].sum())})
    out = pd.DataFrame(rows)
    return out[out["volume"] >= min_volume].reset_index(drop=True)  # chhote farzi zone hatao


def iceberg_forward_test(d, zones, horizon=500):
    res = []
    for _, z in zones.iterrows():
        j = int(z["end"]) + horizon
        if j >= len(d) or z["dir"] == 0:
            continue
        r = (d["price"].iloc[j] / d["price"].iloc[int(z["end"])] - 1) * 1e4 * z["dir"]
        res.append(r)
    if not res:
        return {"zones": 0, "mean_bps": 0.0, "hit%": 0.0}
    res = np.array(res)
    return {"zones": len(res), "mean_bps": round(float(res.mean()), 2),
            "hit%": round(float((res > 0).mean()) * 100, 1)}


# =====================================================================
# 5. MARKET MAKING SIMULATION (sirf simulation, tick data par)
# =====================================================================
def market_making_sim(ticks, half_spread=0.10, max_inv=20, lot=1,
                      fee_per_unit=0.01):
    px = ticks["price"].values
    cash, inv = 0.0, 0
    inv_hist, pnl_hist, fills = [], [], 0
    for i in range(1, len(px)):
        ref = px[i - 1]                          # pichhla price (look-ahead nahi)
        bid, ask = ref - half_spread, ref + half_spread
        if px[i] <= bid and inv < max_inv:
            cash -= bid * lot + fee_per_unit * lot
            inv += lot
            fills += 1
        elif px[i] >= ask and inv > -max_inv:
            cash += ask * lot - fee_per_unit * lot
            inv -= lot
            fills += 1
        inv_hist.append(inv)
        pnl_hist.append(cash + inv * px[i])
    pnl = np.array(pnl_hist)
    return {"Fills": fills, "Final PnL (Rs/unit)": round(float(pnl[-1]), 2),
            "Max Inventory": int(np.max(np.abs(inv_hist))),
            "Worst Drawdown (Rs)": round(float((pnl - np.maximum.accumulate(pnl)).min()), 2)}


# =====================================================================
# MAIN
# =====================================================================
def main():
    print("=" * 60)
    print("BACKTEST LAB (sirf research - nakli data)")
    print("=" * 60)
    summary = []

    # 1. Pairs
    px = synthetic_pair()
    pr, pos = pairs_backtest(px)
    m = metrics(pr.iloc[250:])          # training ke 250 din hata kar
    summary.append({"Strategy": "Pairs / Stat Arb", **m})
    print("\n[1] Pairs / Stat Arb:", m,
          "| trades:", int((pos.diff().abs() > 0).sum()))

    # 2. Reversal + Turnover
    close, vol = synthetic_universe()
    rt = reversal_turnover_backtest(close, vol)
    m = metrics(rt)
    summary.append({"Strategy": "Reversal + Turnover", **m})
    print("[2] Reversal + Turnover:", m)

    save_equity_chart({"Pairs": pr, "Reversal+Turnover": rt},
                      "Equity curves (nakli data)", "equity_curves.png")

    # 3. Execution
    ex = execution_sim()
    ex.to_csv(os.path.join(OUT, "execution_sim.csv"), index=False)
    print("\n[3] VWAP/TWAP execution (kam slippage = behtar):")
    print(ex.to_string(index=False))

    # 4. Iceberg
    ticks = synthetic_ticks()
    d = detect_iceberg(ticks)
    zones = merge_zones(d)
    fwd = iceberg_forward_test(d, zones)
    zones.to_csv(os.path.join(OUT, "iceberg_zones.csv"), index=False)
    print("\n[4] Iceberg zones mile:", len(zones))
    print("    Aage ke 500 tick ka test:", fwd)

    plt.figure(figsize=(10, 5))
    plt.plot(d["price"].values, lw=0.6, label="Price")
    for _, z in zones.iterrows():
        plt.axvspan(z["start"], z["end"], alpha=0.3,
                    color="green" if z["dir"] > 0 else "red")
    plt.title("Iceberg zones (hara = chhupa kharidar, laal = chhupa becchne wala)")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, "iceberg_chart.png"), dpi=150)
    plt.close()

    # 5. Market making
    mm = market_making_sim(ticks)
    print("\n[5] Market-making simulation:", mm)

    pd.DataFrame(summary).to_csv(os.path.join(OUT, "summary.csv"), index=False)
    print("\nSab report '%s' folder me save ho gayi." % OUT)


if __name__ == "__main__":
    main()
