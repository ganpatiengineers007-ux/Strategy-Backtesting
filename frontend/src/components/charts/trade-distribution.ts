import { esc } from "../data-table";

export function tradeDistribution(pnls: number[], bins = 10): string {
  if (!pnls.length) return "<p>No trades</p>";
  const lo = Math.min(...pnls);
  const width = (Math.max(...pnls) - lo || 1) / bins;
  const counts = new Array<number>(bins).fill(0);
  for (const p of pnls) counts[Math.min(bins - 1, Math.floor((p - lo) / width))]++;
  const top = Math.max(...counts);
  return counts.map((c, i) => `<div>${esc((lo + i * width).toFixed(0))} <span style="display:inline-block;background:#2563eb;height:8px;width:${(c / top) * 200}px"></span> ${c}</div>`).join("");
}
