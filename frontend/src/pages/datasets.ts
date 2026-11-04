import { listDatasets } from "../api/datasets";
import { mountPage } from "../components/page";
import { Raw, renderTable } from "../components/data-table";
import { syntheticBadge } from "../components/status-badge";

export function render(el: HTMLElement): Promise<void> {
  return mountPage(el, "Datasets", async () => {
    const rows = (await listDatasets()).map((d) => ({
      file: d.file,
      bars: d.bars,
      quality: d.quality_status,
      data: new Raw(syntheticBadge(d.synthetic) || '<span class="badge unknown">REAL / UNVERIFIED</span>'),
      range: `${d.start_time ?? "?"} to ${d.end_time ?? "?"}`,
      hash: `${d.content_hash.slice(0, 12)}...`,
    }));
    return `<div class="notice">${syntheticBadge(true)} Files under <code>data/samples</code> are synthetic random-walk data and are always labelled here.</div>` +
      renderTable(rows);
  });
}
