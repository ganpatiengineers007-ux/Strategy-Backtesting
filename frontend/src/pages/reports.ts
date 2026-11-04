import { getReport } from "../api/reports";
import { mountPage, card } from "../components/page";
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
    return card(
      `<p>${statusBadge(r.status)} validation: ${statusBadge(String(validation?.status ?? "UNKNOWN"))} ${syntheticBadge(r.synthetic)}</p>` +
      (r.synthetic ? `<div class="notice">${syntheticBadge(true)} डेटासेट <code>${esc(r.dataset_id ?? "unknown")}</code> सिंथेटिक रैंडम-वॉक डेटा है। निष्पादन/वायरिंग साबित करता है, उत्पादन बढ़त नहीं।</div>` : "") +
      (blocked ? `<div class="notice warn"><b>ब्लॉक्ड:</b> ${esc(r.reason ?? "कोई कारण दर्ज नहीं है")}</div>` : "") +
      `<div class="grid">${cards}</div>` +
      `<h3>इक्विटी</h3>${equityCurve(eq)}<h3>ड्रॉडाउन %</h3>${drawdownChart(eq)}<h3>मासिक</h3>${monthlyReturns(eq)}` +
      `<h3>ट्रेड PnL</h3>${tradeDistribution(pnls)}<h3>सत्यापन जांचें</h3>` +
      renderTable(Object.entries(validation?.checks ?? {}).map(([check, x]: [string, any]) => ({ check, status: x.status, reason: x.reason ?? "" }))) +
      `<h3>सभी मेट्रिक</h3>` + renderTable(Object.entries(m).map(([metric, value]) => ({ metric, value: JSON.stringify(value) })))
    );
  });
}
