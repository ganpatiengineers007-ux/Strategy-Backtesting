import { esc } from "./data-table";

export function metricCard(label: string, value: unknown): string {
  const v = typeof value === "number" ? value.toFixed(2) : String(value ?? "-");
  return `<div class="card"><small>${esc(label)}</small><div><b>${esc(v)}</b></div></div>`;
}
