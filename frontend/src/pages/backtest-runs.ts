import { listRuns } from "../api/backtests";
import { mountPage } from "../components/page";
import { runsTable } from "../components/runs-table";

export function render(el: HTMLElement): Promise<void> {
  return mountPage(el, "Backtest runs", async () => runsTable((await listRuns()).reverse()) + '<p><a href="#new-run">+ New run</a></p>');
}
