import { getRun } from "../api/backtests";
import { mountPage, card } from "../components/page";
import { renderKeyValues, esc } from "../components/data-table";
import { statusBadge, syntheticBadge } from "../components/status-badge";

export function render(el: HTMLElement, id = ""): Promise<void> {
  return mountPage(el, `Run: ${id}`, async () => {
    const r = await getRun(id);
    return card(
      `<p>${statusBadge(String(r.status ?? "UNKNOWN"))} ${syntheticBadge(r.synthetic)}</p>` +
      (r.reason ? `<div class="notice warn"><b>Reason:</b> ${esc(r.reason)}</div>` : "") +
      renderKeyValues(r) + `<p><a href="#report/${esc(id)}">report</a> | <a href="#validation/${esc(id)}">validation</a></p>`
    );
  });
}
