import { getValidation } from "../api/validation";
import { mountPage, card } from "../components/page";
import { esc, renderTable } from "../components/data-table";
import { statusBadge, syntheticBadge } from "../components/status-badge";

export function render(el: HTMLElement, id = ""): Promise<void> {
  return mountPage(el, `सत्यापन: ${id}`, async () => {
    const v = await getValidation(id);
    const rows = Object.entries(v.checks ?? {}).map(([check, r]: [string, any]) => ({ check, status: r.status, reason: r.reason ?? "" }));
    return card(
      `<p>कुल मिलाकर: ${statusBadge(String(v.status))} ${syntheticBadge(v.synthetic)} ${esc(v.reason ?? "")}</p>` +
      (v.synthetic ? `<div class="notice">${syntheticBadge(true)} सत्यापन सैंपल डेटा पर चलाया गया था।</div>` : "") +
      renderTable(rows)
    );
  });
}
