import { esc } from "./data-table";

export function metricCard(label: string, value: unknown): string {
  const v = typeof value === "number" ? String(Math.round(value)) : String(value ?? "-");
  return `<div class="card kpi"><small>${esc(label)}</small><div><b>${esc(v)}</b></div></div>`;
}
