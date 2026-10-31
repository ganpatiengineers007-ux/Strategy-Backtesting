import { listDatasets } from "../api/datasets";
import { mountPage } from "../components/page";
import { renderTable } from "../components/data-table";

export function render(el: HTMLElement): Promise<void> {
  return mountPage(el, "Datasets", async () => renderTable(await listDatasets()));
}
