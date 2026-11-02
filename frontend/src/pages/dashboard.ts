import { getHealth } from "../api/health";
import { listRuns } from "../api/backtests";
import { hubStatus } from "../api/hub";
import { mountPage } from "../components/page";
import { statusBadge } from "../components/status-badge";
import { runsTable } from "../components/runs-table";

export function render(el: HTMLElement): Promise<void> {
  return mountPage(el, "Dashboard", async () => {
    const [health, runs] = await Promise.all([getHealth(), listRuns()]);
    let hub = "<p>Hub: <a href=\"#live\">Live page</a> par dekho</p>";
    try {
      const h = await hubStatus();
      const live = h.last_quote_age_s !== null && h.last_quote_age_s <= 30;
      hub = `<p>Hub: ${statusBadge(live ? "PASS" : "FAIL")} ${live ? "LIVE" : "STALE / band"} | quotes ${h.quotes} | candle series ${h.candle_series}</p>`;
    } catch {
      /* hub abhi taiyaar nahi - dashboard phir bhi dikhe */
    }
    return `<p>API: ${statusBadge(health.status)}</p>${hub}<h3>Latest runs</h3>` + runsTable(runs.slice(-10).reverse());
  });
}
