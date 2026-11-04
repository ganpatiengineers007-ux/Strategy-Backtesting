import { getValidation } from "../api/validation";
import { mountPage } from "../components/page";
import { esc, renderTable } from "../components/data-table";
import { statusBadge, syntheticBadge } from "../components/status-badge";

export function render(el: HTMLElement, id = ""): Promise<void> {
  return mountPage(el, `Validation: ${id}`, async () => {
    const v = await getValidation(id);
    const rows = Object.entries(v.checks ?? {}).map(([check, r]: [string, any]) => ({ check, status: r.status, reason: r.reason ?? "" }));
    return `<p>Overall: ${statusBadge(String(v.status))} ${syntheticBadge(v.synthetic)} ${esc(v.reason ?? "")}</p>` +
      (v.synthetic ? `<div class="notice">${syntheticBadge(true)} Validation ran on synthetic sample data.</div>` : "") +
      renderTable(rows);
  });
}
