import { listStrategies } from "../api/strategies";
import { mountPage } from "../components/page";
import { esc, renderTable } from "../components/data-table";

export function render(el: HTMLElement): Promise<void> {
  return mountPage(el, "Strategies", async () => {
    const rows = (await listStrategies()).map((s) => ({ id: s.id, version: s.version, required_data: s.required_data.join(", ") || "-", detail: `<a href="#strategy/${esc(s.id)}">open</a>` }));
    return renderTable(rows).replace(/&lt;a href=&quot;#strategy\/([\w.-]+)&quot;&gt;open&lt;\/a&gt;/g, '<a href="#strategy/$1">open</a>');
  });
}
