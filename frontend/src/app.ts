import { navigation } from "./components/navigation";
import { runLeave } from "./components/page";
import * as dashboard from "./pages/dashboard";
import * as live from "./pages/live";
import * as newRun from "./pages/new-run";
import * as settings from "./pages/settings";
import * as registry from "./pages/strategy-registry";
import * as strategyDetail from "./pages/strategy-detail";
import * as createStrategy from "./pages/create-strategy";
import * as runs from "./pages/backtest-runs";
import * as runDetail from "./pages/backtest-detail";
import * as validation from "./pages/validation-results";
import * as comparison from "./pages/comparison";
import * as reports from "./pages/reports";
import * as datasets from "./pages/datasets";
import * as health from "./pages/system-health";
import * as audit from "./pages/audit-log";

type Page = { render: (el: HTMLElement, arg?: string) => Promise<void> };

const ROUTES: Record<string, Page> = {
  dashboard, live, "new-run": newRun, settings, strategies: registry, strategy: strategyDetail, "create-strategy": createStrategy, runs, run: runDetail,
  validation, compare: comparison, report: reports, datasets, health, audit,
};

export function start(el: HTMLElement, nav: HTMLElement): void {
  nav.innerHTML = navigation();
  const go = (): void => {
    runLeave();
    const [name, ...rest] = (location.hash.slice(1) || "dashboard").split("/");
    void (ROUTES[name] ?? dashboard).render(el, decodeURIComponent(rest.join("/")));
  };
  window.addEventListener("hashchange", go);
  go();
}
