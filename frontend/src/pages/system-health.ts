import { getHealth } from "../api/health";
import { mountPage } from "../components/page";
import { renderKeyValues } from "../components/data-table";

export function render(el: HTMLElement): Promise<void> {
  return mountPage(el, "System health", async () => renderKeyValues(await getHealth()));
}
