import { compareRuns } from "../api/comparisons";
import { mountPage } from "../components/page";
import { renderTable } from "../components/data-table";

export function render(el: HTMLElement, ids = ""): Promise<void> {
  return mountPage(el, "Compare runs", async () => {
    const runIds = ids.split(",").map((s) => s.trim()).filter(Boolean);
    if (runIds.length < 2) return "<p>URL: <code>#compare/runid1,runid2</code></p>";
    const c = await compareRuns(runIds);
    const rows = (c.metric_names as string[]).map((m) => ({ metric: m, ...Object.fromEntries(c.runs.map((r: any) => [r.run_id, r.metrics[m]])) }));
    return renderTable(rows);
  });
}
