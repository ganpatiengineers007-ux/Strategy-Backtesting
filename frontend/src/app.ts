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
import * as login from "./pages/login";
import { getJson } from "./api/client";

type Page = { render: (el: HTMLElement, arg?: string) => Promise<void> };

const PUBLIC_ROUTES = new Set(["login"]);
const ROUTES: Record<string, Page> = {
  dashboard, live, "new-run": newRun, settings, strategies: registry, strategy: strategyDetail, "create-strategy": createStrategy, runs, run: runDetail,
  validation, compare: comparison, report: reports, datasets, health, audit, login,
};

let currentUser: string | null = null;
let authChecked = false;

async function checkAuth(): Promise<boolean> {
  try {
    const res = await getJson<{ authenticated: boolean; user: string | null }>("/auth/me");
    currentUser = res.authenticated ? res.user : null;
    return res.authenticated;
  } catch {
    currentUser = null;
    return false;
  }
}

function updateNav(): void {
  const nav = document.querySelector("nav");
  if (!nav) return;

  if (currentUser) {
    nav.innerHTML = navigation() + ` <span style="margin-left: auto; padding: 8px 12px; color: var(--muted); font-size: 14px;">${currentUser}</span> ` +
      `<button id="logout-btn" style="margin-left: 8px;">Logout</button>`;
    nav.querySelector("#logout-btn")?.addEventListener("click", async () => {
      try {
        await fetch("/auth/logout", { method: "POST", credentials: "include" });
      } catch { /* ignore */ }
      currentUser = null;
      location.hash = "#login";
    });
  } else {
    nav.innerHTML = "";
  }
}

export async function start(el: HTMLElement, nav: HTMLElement): Promise<void> {
  const go = async (): Promise<void> => {
    runLeave();
    const [name, ...rest] = (location.hash.slice(1) || "dashboard").split("/");
    const routeName = name || "dashboard";

    if (!authChecked) {
      await checkAuth();
      authChecked = true;
    }

    const isPublic = PUBLIC_ROUTES.has(routeName);
    if (!isPublic && !currentUser) {
      location.hash = "#login";
      return;
    }

    if (routeName === "login" && currentUser) {
      location.hash = "#dashboard";
      return;
    }

    updateNav();
    void (ROUTES[routeName] ?? dashboard).render(el, decodeURIComponent(rest.join("/")));
  };

  window.addEventListener("hashchange", go);
  await go();
}