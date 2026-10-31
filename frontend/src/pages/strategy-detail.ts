import { getStrategy } from "../api/strategies";
import { mountPage } from "../components/page";
import { renderKeyValues } from "../components/data-table";

export function render(el: HTMLElement, id = ""): Promise<void> {
  return mountPage(el, `Strategy: ${id}`, async () => renderKeyValues(await getStrategy(id) as unknown as Record<string, unknown>));
}
