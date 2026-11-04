import { compareRuns } from "../api/comparisons";
import { mountPage, card } from "../components/page";
import { Raw, esc, renderTable } from "../components/data-table";
import { statusBadge, syntheticBadge } from "../components/status-badge";

export function render(el: HTMLElement, ids = ""): Promise<void> {
  return mountPage(el, "Compare runs", async () => {
    const form = `<p><input id="cmp-ids" size="40" placeholder="runid1,runid2" value="${esc(ids)}"> <button id="cmp-go">Compare</button></p>`;
    const runIds = ids.split(",").map((s) => s.trim()).filter(Boolean);
    if (runIds.length < 2) return card(form + "<p>Kam se kam 2 run id likho (Runs page से copy karो।</p>");
    const c = await compareRuns(runIds);
    const summary = c.runs.map((r: any) => ({
      run_id: r.run_id,
      status: new Raw(statusBadge(String(r.status))),
      validation: r.validation,
      data: new Raw(syntheticBadge(r.synthetic) || '<span class="badge unknown">REAL / UNVERIFIED</span>'),
      reason: r.reason ?? "",
    }));
    const rows = (c.metric_names as string[]).map((m) => ({ metric: m, ...Object.fromEntries(c.runs.map((r: any) => [r.run_id, r.metrics[m]])) }));
    const synthetic = c.runs.some((r: any) => r.synthetic);
    return card(form + (synthetic ? `<div class="notice">${syntheticBadge(true)} कम से कम एक रन सैंपल डेटा पर चलाया गया है।</div>` : "") +
      renderTable(summary) + renderTable(rows));
  }).then(() => {
    el.querySelector("#cmp-go")?.addEventListener("click", () => {
      const v = (el.querySelector("#cmp-ids") as HTMLInputElement).value.replace(/\s+/g, "");
      location.hash = `#compare/${encodeURIComponent(v)}`;
    });
  });
}
