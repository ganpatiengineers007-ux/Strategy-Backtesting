import { getReport } from "../api/reports";
import { mountPage } from "../components/page";
import { renderTable } from "../components/data-table";
import { metricCard } from "../components/metric-card";
import { statusBadge } from "../components/status-badge";
import { equityCurve } from "../components/charts/equity-curve";
import { drawdownChart } from "../components/charts/drawdown-chart";
import { monthlyReturns } from "../components/charts/monthly-returns";
import { tradeDistribution } from "../components/charts/trade-distribution";

export function render(el: HTMLElement, id = ""): Promise<void> {
  return mountPage(el, `Report: ${id}`, async () => {
    const r = await getReport(id);
    const m = r.metrics as Record<string, unknown>;
    const cards = ["total_return_pct", "max_drawdown_pct", "n_trades", "win_rate_pct", "expectancy"].map((k) => metricCard(k, m[k])).join("");
    const eq = (r.equity ?? []) as [string, number][];
    const pnls = ((r.trades ?? []) as { pnl: number }[]).map((t) => t.pnl);
    return `<p>${statusBadge(r.status)} validation: ${statusBadge(String((r.validation as any).status))}</p><div class="grid">${cards}</div>` +
      `<h3>Equity</h3>${equityCurve(eq)}<h3>Drawdown %</h3>${drawdownChart(eq)}<h3>Monthly</h3>${monthlyReturns(eq)}` +
      `<h3>Trade PnL</h3>${tradeDistribution(pnls)}<h3>All metrics</h3>` + renderTable(Object.entries(m).map(([metric, value]) => ({ metric, value: JSON.stringify(value) })));
  });
}
