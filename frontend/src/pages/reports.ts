import { getReport } from "../api/reports";
import { mountPage } from "../components/page";
import { esc, renderTable } from "../components/data-table";
import { metricCard } from "../components/metric-card";
import { statusBadge, syntheticBadge } from "../components/status-badge";
import { equityCurve } from "../components/charts/equity-curve";
import { drawdownChart } from "../components/charts/drawdown-chart";
import { monthlyReturns } from "../components/charts/monthly-returns";
import { tradeDistribution } from "../components/charts/trade-distribution";

export function render(el: HTMLElement, id = ""): Promise<void> {
  return mountPage(el, `Report: ${id}`, async () => {
    const r = await getReport(id);
    const m = r.metrics as Record<string, unknown>;
    const validation = r.validation as any;
    const cards = ["total_return_pct", "max_drawdown_pct", "n_trades", "win_rate_pct", "expectancy"].map((k) => metricCard(k, m[k])).join("");
    const eq = (r.equity ?? []) as [string, number][];
    const pnls = ((r.trades ?? []) as { pnl: number }[]).map((t) => t.pnl);
    const blocked = r.status === "BLOCKED";
    return `<p>${statusBadge(r.status)} validation: ${statusBadge(String(validation?.status ?? "UNKNOWN"))} ${syntheticBadge(r.synthetic)}</p>` +
      (r.synthetic ? `<div class="notice">${syntheticBadge(true)} Dataset <code>${esc(r.dataset_id ?? "unknown")}</code> is synthetic random-walk data. Results prove execution/wiring, not production edge.</div>` : "") +
      (blocked ? `<div class="notice warn"><b>BLOCKED:</b> ${esc(r.reason ?? "no reason recorded")}</div>` : "") +
      `<div class="grid">${cards}</div>` +
      `<h3>Equity</h3>${equityCurve(eq)}<h3>Drawdown %</h3>${drawdownChart(eq)}<h3>Monthly</h3>${monthlyReturns(eq)}` +
      `<h3>Trade PnL</h3>${tradeDistribution(pnls)}<h3>Validation checks</h3>` +
      renderTable(Object.entries(validation?.checks ?? {}).map(([check, x]: [string, any]) => ({ check, status: x.status, reason: x.reason ?? "" }))) +
      `<h3>All metrics</h3>` + renderTable(Object.entries(m).map(([metric, value]) => ({ metric, value: JSON.stringify(value) })));
  });
}
