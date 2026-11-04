import { esc } from "./data-table";

export function errorPanel(message: string): string {
  return `<div class="error">${esc(message)}</div>`;
}
