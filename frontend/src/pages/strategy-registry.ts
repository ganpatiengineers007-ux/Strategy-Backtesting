import { listStrategies } from "../api/strategies";
import { mountPage } from "../components/page";
import { Raw, esc, renderTable } from "../components/data-table";
import { readinessBadge } from "../components/status-badge";

export function render(el: HTMLElement): Promise<void> {
  return mountPage(el, "Strategies", async () => {
    const rows = (await listStrategies()).map((s) => ({
      id: s.id,
      version: s.version,
      status: new Raw(readinessBadge(s.status)),
      reason: s.reason || s.data_hint || "-",
      required_data: s.required_data.join(", ") || "-",
      detail: new Raw(`<a href="#strategy/${esc(s.id)}">open</a>`),
    }));
    return `<div class="notice warn">BLOCKED strategies are never faked. They require data or engine support listed below.</div>` + renderTable(rows);
  });
}
