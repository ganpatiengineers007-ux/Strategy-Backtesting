import { getHealth } from "../api/health";
import { listRuns } from "../api/backtests";
import { listDatasets } from "../api/datasets";
import { listStrategies } from "../api/strategies";
import { hubStatus } from "../api/hub";
import { mountPage } from "../components/page";
import { Raw, esc, renderTable } from "../components/data-table";
import { metricCard } from "../components/metric-card";
import { statusBadge, readinessBadge, syntheticBadge } from "../components/status-badge";
import { runsTable } from "../components/runs-table";

export function render(el: HTMLElement): Promise<void> {
  return mountPage(el, "Dashboard", async () => {
    const [health, runs, strategies, datasets] = await Promise.all([
      getHealth(), listRuns(), listStrategies(), listDatasets(),
    ]);
    const runnable = strategies.filter((s) => s.runnable).length;
    const blocked = strategies.length - runnable;
    const synthetic = datasets.filter((d) => d.synthetic).length;
    let hub = '<p>Hub: <a href="#live">Live page</a> par dekho</p>';
    try {
      const h = await hubStatus();
      const live = h.last_quote_age_s !== null && h.last_quote_age_s <= 30;
      hub = `<p>Hub: ${statusBadge(live ? "PASS" : "FAIL")} ${live ? "LIVE" : "STALE / band"} | quotes ${h.quotes} | candle series ${h.candle_series}</p>`;
    } catch {
      hub = '<p>Hub: <span class="badge blocked">NOT INITIALIZED</span> Live market data is optional; sample backtests do not need it.</p>';
    }
    const strategyRows = strategies.map((s) => ({
      strategy: s.id,
      status: new Raw(readinessBadge(s.status)),
      reason: s.reason || s.data_hint || "-",
      live: s.live_trading_enabled ? "ENABLED" : "disabled",
      open: new Raw(`<a href="#strategy/${esc(s.id)}">detail</a>`),
    }));
    return `<p>API: ${statusBadge(health.status)}</p>${hub}` +
      `<div class="grid">${metricCard("strategies", strategies.length)}${metricCard("runnable", runnable)}${metricCard("blocked", blocked)}${metricCard("synthetic datasets", synthetic)}</div>` +
      (synthetic ? `<div class="notice">${syntheticBadge(true)} Sample datasets are synthetic random-walk data. They prove execution/wiring, not market edge.</div>` : "") +
      `<h3>Strategy readiness</h3>` + renderTable(strategyRows) +
      `<h3>Latest runs</h3>` + runsTable(runs.slice(-10).reverse());
  });
}
