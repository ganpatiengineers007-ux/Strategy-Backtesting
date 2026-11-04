import { getStrategy } from "../api/strategies";
import { mountPage, card } from "../components/page";
import { renderKeyValues } from "../components/data-table";
import { readinessBadge } from "../components/status-badge";

export function render(el: HTMLElement, id = ""): Promise<void> {
  return mountPage(el, `Strategy: ${id}`, async () => {
    const s = await getStrategy(id);
    const head = `<p>स्थिति: ${readinessBadge(s.status)} ${s.live_trading_enabled ? '<span class="badge fail">लाइव ट्रेडिंग सक्षम</span>' : '<span class="badge runnable">लाइव ट्रेडिंग बंद</span>'}</p>` +
      (s.reason ? `<div class="notice warn"><b>ब्लॉक्ड कारण:</b> ${s.reason}</div>` : "") +
      (s.data_hint ? `<div class="notice">${s.data_hint}</div>` : "");
    const view: Record<string, unknown> = { ...s };
    delete view.status; delete view.runnable; delete view.reason; delete view.data_hint; delete view.blocked_reason;
    view.source_hash = `${String(s.source_hash).slice(0, 16)}...`;
    return card(head + renderKeyValues(view));
  });
}
