import { getValidation } from "../api/validation";
import { mountPage } from "../components/page";
import { renderTable } from "../components/data-table";
import { statusBadge } from "../components/status-badge";

export function render(el: HTMLElement, id = ""): Promise<void> {
  return mountPage(el, `Validation: ${id}`, async () => {
    const v = await getValidation(id);
    const rows = Object.entries(v.checks ?? {}).map(([check, r]: [string, any]) => ({ check, status: r.status, reason: r.reason ?? "" }));
    return `<p>Overall: ${statusBadge(v.status)} ${v.reason ?? ""}</p>` + renderTable(rows);
  });
}
