import { getAudit } from "../api/audit";
import { mountPage } from "../components/page";
import { renderTable } from "../components/data-table";

export function render(el: HTMLElement): Promise<void> {
  return mountPage(el, "Audit log", async () => renderTable((await getAudit()).reverse()));
}
