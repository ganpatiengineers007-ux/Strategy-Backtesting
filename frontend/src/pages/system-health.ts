import { getHealth } from "../api/health";
import { hubStatus } from "../api/hub";
import { listStrategies } from "../api/strategies";
import { mountPage } from "../components/page";
import { renderKeyValues } from "../components/data-table";

export function render(el: HTMLElement): Promise<void> {
  return mountPage(el, "System health", async () => {
    const [health, strategies] = await Promise.all([getHealth(), listStrategies()]);
    let hub: Record<string, unknown>;
    try {
      hub = { status: "ok", ...(await hubStatus()) };
    } catch (e) {
      hub = { status: "not_initialized", detail: String(e) };
    }
    const view = {
      api: health.status,
      strategies: strategies.length,
      runnable: strategies.filter((s) => s.runnable).length,
      blocked: strategies.filter((s) => !s.runnable).length,
      hub: JSON.stringify(hub),
      live_trading: "disabled everywhere",
    };
    return renderKeyValues(view);
  });
}
