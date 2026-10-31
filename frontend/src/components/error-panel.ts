import { esc } from "./data-table";

export function errorPanel(message: string): string {
  return `<div class="card badge fail">${esc(message)}</div>`;
}
