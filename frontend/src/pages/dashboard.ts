import { getHealth } from "../api/health";
import { listRuns } from "../api/backtests";
import { listDatasets } from "../api/datasets";
import { listStrategies } from "../api/strategies";
import { hubStatus } from "../api/hub";
import { mountPage, card } from "../components/page";
import { Raw, esc, renderTable } from "../components/data-table";
import { metricCard } from "../components/metric-card";
import { statusBadge, readinessBadge, syntheticBadge } from "../components/status-badge";
import { runsTable } from "../components/runs-table";

export function render(el: HTMLElement): Promise<void> {
  return mountPage(el, "Dashboard", async () => {
    const [health, runs, strategies, datasets] = await Promise.all([
      getHealth(), listRuns(), listStrategies(), listDatasets(),
    ]);
    const runnable = strategies.filter((s) => s.runnable).length;
    const blocked = strategies.length - runnable;
    const synthetic = datasets.filter((d) => d.synthetic).length;
    let hub = '<p>Hub: <a href="#live">लाइव पेज पर देखें</a></p>';
    try {
      const h = await hubStatus();
      const live = h.last_quote_age_s !== null && h.last_quote_age_s <= 30;
      hub = `<p>Hub: ${statusBadge(live ? "PASS" : "FAIL")} ${live ? "लाइव" : "स्टेल / बंद"} | quotes ${h.quotes} | कैंडल सीरीज़ ${h.candle_series}</p>`;
    } catch {
      hub = '<p>Hub: <span class="badge blocked">प्रारंभ नहीं हुआ</span> लाइव बाज़ार डेटा वैकल्पिक है; सैंपल बैकटेस्ट को इसकी ज़रूरत नहीं है।</p>';
    }
    const metrics = card(
      `<div class="grid">${metricCard("strategies", strategies.length)}${metricCard("रनबल", runnable)}${metricCard("ब्लॉक्ड", blocked)}${metricCard("सैंपल डेटासेट", synthetic)}</div>` +
      (synthetic ? `<div class="notice">${syntheticBadge(true)} सैंपल डेटासेट सिंथेटिक रैंडम-वॉक डेटा हैं। वे निष्पादन/वायरिंग साबित करते हैं, बाज़ार बढ़त नहीं।</div>` : "")
    );
    const strategyRows = strategies.map((s) => ({
      strategy: s.id,
      status: new Raw(readinessBadge(s.status)),
      reason: s.reason || s.data_hint || "-",
      live: s.live_trading_enabled ? "सक्षम" : "बंद",
      open: new Raw(`<a href="#strategy/${esc(s.id)}">विवरण</a>`),
    }));
    const readiness = card("<h3>रणनीति तत्परता</h3>" + renderTable(strategyRows));
    const latest = card("<h3>नवीनतम रन</h3>" + runsTable(runs.slice(-10).reverse()));
    return `<p>API: ${statusBadge(health.status)}</p>${hub}` + metrics + readiness + latest;
  });
}
