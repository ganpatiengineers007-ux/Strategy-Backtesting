import { getRun } from "../api/backtests";
import { mountPage } from "../components/page";
import { renderKeyValues, esc } from "../components/data-table";

export function render(el: HTMLElement, id = ""): Promise<void> {
  return mountPage(el, `Run: ${id}`, async () =>
    renderKeyValues(await getRun(id)) + `<p><a href="#report/${esc(id)}">report</a> | <a href="#validation/${esc(id)}">validation</a></p>`);
}
