import { listStrategies } from "../api/strategies";
import { mountPage, card } from "../components/page";
import { Raw, esc, renderTable } from "../components/data-table";
import { readinessBadge } from "../components/status-badge";

export function render(el: HTMLElement): Promise<void> {
  return mountPage(el, "रणनीतियां", async () => {
    const rows = (await listStrategies()).map((s) => ({
      id: s.id,
      version: s.version,
      status: new Raw(readinessBadge(s.status)),
      reason: s.reason || s.data_hint || "-",
      required_data: s.required_data.join(", ") || "-",
      detail: new Raw(`<a href="#strategy/${esc(s.id)}">विवरण</a>`),
    }));
    return card(
      '<div class="notice warn">ब्लॉक्ड रणनीतियों को कभी नकली नहीं बनाया जाता। उन्हें नीचे सूचीबद्ध डेटा या इंजन सहायता की आवश्यकता होती है।</div>' + renderTable(rows)
    );
  });
}
