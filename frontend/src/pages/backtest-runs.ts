import { listRuns } from "../api/backtests";
import { mountPage } from "../components/page";
import { renderTable } from "../components/data-table";

export function render(el: HTMLElement): Promise<void> {
  return mountPage(el, "Backtest runs", async () => renderTable((await listRuns()).reverse()) + "<p>Detail: <code>#run/&lt;run_id&gt;</code></p>");
}
