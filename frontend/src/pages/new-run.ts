import { getRun, startRun } from "../api/backtests";
import { listDatasets } from "../api/datasets";
import { listStrategies } from "../api/strategies";
import { mountPage } from "../components/page";
import { esc } from "../components/data-table";
import { errorPanel } from "../components/error-panel";

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export function render(el: HTMLElement): Promise<void> {
  return mountPage(el, "New backtest", async () => {
    const [strategies, datasets] = await Promise.all([listStrategies(), listDatasets()]);
    if (!datasets.length) return "<p>Koi CSV dataset nahi mila. DATA_DIR me CSV rakho (hub se: <code>python -m fyers_hub export SYMBOL TF --out file.csv</code>).</p>";
    const opt = (v: unknown, label: unknown) => `<option value="${esc(v)}">${esc(label ?? v)}</option>`;
    return `<p>Strategy<br><select id="nr-strat">${strategies.map((s) => opt(s.id, `${s.status === "BLOCKED" ? "[BLOCKED] " : ""}${s.id}`)).join("")}</select></p>` +
      `<div id="nr-warn"></div>` +
      `<p>Dataset (CSV)<br><select id="nr-data">${datasets.map((d) => opt(d.file, `${d.synthetic ? "[SYNTHETIC] " : ""}${d.file}`)).join("")}</select></p>` +
      `<p>Symbol<br><input id="nr-sym" value="NIFTY"></p><p>Timeframe<br><input id="nr-tf" value="1m"></p>` +
      `<p><button id="nr-go">Run backtest</button></p><div id="nr-msg"></div>`;
  }).then(() => {
    const v = (id: string) => (el.querySelector(`#${id}`) as HTMLInputElement | null)?.value ?? "";
    const msg = el.querySelector("#nr-msg") as HTMLElement | null;
    const warn = el.querySelector("#nr-warn") as HTMLElement | null;
    const showWarn = async (): Promise<void> => {
      if (!warn) return;
      const strategies = await listStrategies();
      const s = strategies.find((x) => x.id === v("nr-strat"));
      warn.innerHTML = s?.status === "BLOCKED"
        ? `<div class="notice warn"><b>BLOCKED:</b> ${esc(s.reason)} The API will return status BLOCKED, not fake metrics.</div>`
        : s?.data_hint ? `<div class="notice">${esc(s.data_hint)}</div>` : "";
    };
    el.querySelector("#nr-strat")?.addEventListener("change", () => void showWarn());
    void showWarn();
    el.querySelector("#nr-go")?.addEventListener("click", async () => {
      if (!msg) return;
      msg.textContent = "Chal raha hai...";
      try {
        let job = await startRun({ strategy_id: v("nr-strat"), dataset: v("nr-data"), symbol: v("nr-sym"), timeframe: v("nr-tf") });
        const deadline = Date.now() + 180_000;
        while (!job.result?.run_id && !job.error && Date.now() < deadline) {
          await sleep(1000);
          job = await getRun(job.job_id);
        }
        if (job.result?.run_id) location.hash = `#report/${encodeURIComponent(job.result.run_id)}`;
        else msg.innerHTML = errorPanel(String(job.error ?? `status: ${job.status}`));
      } catch (e) {
        msg.innerHTML = errorPanel(String(e));
      }
    });
  });
}
