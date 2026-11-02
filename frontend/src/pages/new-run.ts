import { startRun } from "../api/backtests";
import { listDatasets } from "../api/datasets";
import { listStrategies } from "../api/strategies";
import { mountPage } from "../components/page";
import { esc } from "../components/data-table";
import { errorPanel } from "../components/error-panel";

export function render(el: HTMLElement): Promise<void> {
  return mountPage(el, "New backtest", async () => {
    const [strategies, datasets] = await Promise.all([listStrategies(), listDatasets()]);
    if (!datasets.length) return "<p>Koi CSV dataset nahi mila. DATA_DIR me CSV rakho (hub se: <code>python -m fyers_hub export SYMBOL TF --out file.csv</code>).</p>";
    const opt = (v: unknown, label?: unknown) => `<option value="${esc(v)}">${esc(label ?? v)}</option>`;
    return `<p>Strategy<br><select id="nr-strat">${strategies.map((s) => opt(s.id)).join("")}</select></p>` +
      `<p>Dataset (CSV)<br><select id="nr-data">${datasets.map((d) => opt(d.file)).join("")}</select></p>` +
      `<p>Symbol<br><input id="nr-sym" value="NIFTY"></p><p>Timeframe<br><input id="nr-tf" value="1m"></p>` +
      `<p><button id="nr-go">Run backtest</button></p><div id="nr-msg"></div>`;
  }).then(() => {
    const v = (id: string) => (el.querySelector(`#${id}`) as HTMLInputElement | null)?.value ?? "";
    const msg = el.querySelector("#nr-msg") as HTMLElement | null;
    el.querySelector("#nr-go")?.addEventListener("click", async () => {
      if (!msg) return;
      msg.textContent = "Chal raha hai...";
      try {
        const job = await startRun({ strategy_id: v("nr-strat"), dataset: v("nr-data"), symbol: v("nr-sym"), timeframe: v("nr-tf") });
        if (job.result?.run_id) location.hash = `#report/${encodeURIComponent(job.result.run_id)}`;
        else msg.innerHTML = errorPanel(String(job.error ?? `status: ${job.status}`));
      } catch (e) {
        msg.innerHTML = errorPanel(String(e));
      }
    });
  });
}
