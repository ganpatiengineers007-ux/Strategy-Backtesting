import { compareRuns } from "../api/comparisons";
import { mountPage } from "../components/page";
import { esc, renderTable } from "../components/data-table";

export function render(el: HTMLElement, ids = ""): Promise<void> {
  return mountPage(el, "Compare runs", async () => {
    const form = `<p><input id="cmp-ids" size="40" placeholder="runid1,runid2" value="${esc(ids)}"> <button id="cmp-go">Compare</button></p>`;
    const runIds = ids.split(",").map((s) => s.trim()).filter(Boolean);
    if (runIds.length < 2) return form + "<p>Kam se kam 2 run id likho (Runs page se copy karo).</p>";
    const c = await compareRuns(runIds);
    const rows = (c.metric_names as string[]).map((m) => ({ metric: m, ...Object.fromEntries(c.runs.map((r: any) => [r.run_id, r.metrics[m]])) }));
    return form + renderTable(rows);
  }).then(() => {
    el.querySelector("#cmp-go")?.addEventListener("click", () => {
      const v = (el.querySelector("#cmp-ids") as HTMLInputElement).value.replace(/\s+/g, "");
      location.hash = `#compare/${encodeURIComponent(v)}`;
    });
  });
}
