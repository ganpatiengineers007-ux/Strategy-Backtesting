import { esc } from "./data-table";

export function statusBadge(status: string): string {
  const cls = String(status).toLowerCase();
  return `<span class="badge ${esc(cls)}">${esc(status)}</span>`;
}

export function syntheticBadge(synthetic: boolean | undefined, label = "SYNTHETIC DATA"): string {
  return synthetic ? `<span class="badge synthetic">${esc(label)}</span>` : "";
}

export function readinessBadge(status: string | undefined): string {
  const s = String(status ?? "UNKNOWN").toUpperCase();
  return statusBadge(s);
}
