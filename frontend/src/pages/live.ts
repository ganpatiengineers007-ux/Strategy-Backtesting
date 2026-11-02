import { ChainRow, hubCandles, hubChain, hubQuotes, hubStatus } from "../api/hub";
import { lineChartSvg } from "../components/chart-panel";
import { esc, renderTable } from "../components/data-table";
import { errorPanel } from "../components/error-panel";
import { metricCard } from "../components/metric-card";
import { onLeave } from "../components/page";
import { statusBadge } from "../components/status-badge";

const st = { symbol: "NSE:NIFTY50-INDEX", tf: "1", und: "NSE:NIFTY50-INDEX" };
const n = (v: unknown, d = 2) => (typeof v === "number" ? v.toFixed(d) : "-");

function chainTable(spot: number | null, rows: ChainRow[]): string {
  if (!rows.length || spot === null) return "<p>Option chain abhi hub me nahi hai. Server par <code>python -m fyers_hub chain</code> ya <code>live</code> chalao.</p>";
  const strikes = [...new Set(rows.map((r) => r.strike))].sort((a, b) => a - b);
  const atm = strikes.reduce((b, k) => (Math.abs(k - spot) < Math.abs(b - spot) ? k : b), strikes[0]);
  const i = strikes.indexOf(atm);
  const pick = (k: number, t: string) => rows.find((r) => r.strike === k && r.opt_type === t);
  const out = strikes.slice(Math.max(0, i - 6), i + 7).map((k) => {
    const ce = pick(k, "CE"), pe = pick(k, "PE");
    return { CE_oi: n(ce?.oi, 0), CE_iv: n(ce?.iv), CE_delta: n(ce?.delta), CE_ltp: n(ce?.ltp), strike: k === atm ? `[${k}]` : k,
      PE_ltp: n(pe?.ltp), PE_delta: n(pe?.delta), PE_iv: n(pe?.iv), PE_oi: n(pe?.oi, 0) };
  });
  return `<p>Spot ${n(spot)} | ATM ${atm}</p>` + renderTable(out);
}

async function build(): Promise<string> {
  const [s, quotes, candles, chain] = await Promise.all([hubStatus(), hubQuotes(30), hubCandles(st.symbol, st.tf, 200), hubChain(st.und)]);
  const live = s.last_quote_age_s !== null && s.last_quote_age_s <= 30;
  const last = candles[candles.length - 1];
  const age = s.last_quote_age_s === null ? "-" : `${s.last_quote_age_s}s`;
  return `<p>${statusBadge(live ? "PASS" : "FAIL")} ${live ? "LIVE" : "STALE - live process band hai?"} (last quote ${esc(age)} pehle)</p>` +
    `<div class="grid">${metricCard("quotes", s.quotes)}${metricCard("candle series", s.candle_series)}${metricCard("instruments", s.instruments)}` +
    `${last ? metricCard("last close", last[4]) : ""}</div>` +
    `<h3>${esc(st.symbol)} (${esc(st.tf)})</h3>${lineChartSvg(candles.map((c) => c[4]))}` +
    `<h3>Option chain (ATM +-6)</h3>${chainTable(chain.spot, chain.rows)}` +
    `<h3>Latest quotes</h3>${renderTable(quotes.map((q) => ({ symbol: q.symbol, ltp: q.ltp, change_pct: q.change_pct, volume: q.volume, bid: q.bid, ask: q.ask })))}`;
}

export async function render(el: HTMLElement): Promise<void> {
  const field = (id: string, label: string, v: string) => `<label>${label} <input id="${id}" value="${esc(v)}"></label> `;
  el.innerHTML = `<h2>Live data</h2><p>${field("lv-sym", "Symbol", st.symbol)}${field("lv-tf", "TF", st.tf)}${field("lv-und", "Chain", st.und)}<button id="lv-go">Load</button></p>` +
    `<div id="lv-body">Loading...</div>`;
  const body = el.querySelector("#lv-body") as HTMLElement;
  const val = (id: string) => (el.querySelector(`#${id}`) as HTMLInputElement).value.trim();
  const refresh = async (): Promise<void> => {
    st.symbol = val("lv-sym") || st.symbol;
    st.tf = val("lv-tf") || st.tf;
    st.und = val("lv-und") || st.und;
    try {
      body.innerHTML = await build();
    } catch (e) {
      body.innerHTML = errorPanel(String(e));
    }
  };
  el.querySelector("#lv-go")?.addEventListener("click", () => void refresh());
  await refresh();
  const t = window.setInterval(() => void refresh(), 5000);
  onLeave(() => window.clearInterval(t));
}
