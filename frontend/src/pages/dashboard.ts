import { getHealth } from "../api/health";
import { listRuns } from "../api/backtests";
import { mountPage } from "../components/page";
import { renderTable } from "../components/data-table";
import { statusBadge } from "../components/status-badge";

export function render(el: HTMLElement): Promise<void> {
  return mountPage(el, "Dashboard", async () => {
    const [health, runs] = await Promise.all([getHealth(), listRuns()]);
    return `<p>API: ${statusBadge(health.status)}</p>` + renderTable(runs.slice(-10).reverse());
  });
}
