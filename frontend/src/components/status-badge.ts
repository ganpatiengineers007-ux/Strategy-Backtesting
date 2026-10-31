import { esc } from "./data-table";

export function statusBadge(status: string): string {
  const cls = String(status).toLowerCase();
  return `<span class="badge ${esc(cls)}">${esc(status)}</span>`;
}
