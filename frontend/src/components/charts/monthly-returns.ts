import { renderTable } from "../data-table";

export function monthlyReturns(points: [string, number][]): string {
  const last: Record<string, number> = {};
  for (const [ts, e] of points) last[ts.slice(0, 7)] = e;
  const months = Object.keys(last).sort();
  const rows = months.map((m, i) => ({ month: m, return_pct: i === 0 ? "-" : ((last[m] / last[months[i - 1]] - 1) * 100).toFixed(2) }));
  return renderTable(rows);
}
