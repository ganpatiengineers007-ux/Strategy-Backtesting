import { clearApiKey, hasApiKey, setApiKey } from "../api/client";
import { mountPage } from "../components/page";

export function render(el: HTMLElement): Promise<void> {
  return mountPage(el, "Settings", async () =>
    `<p>API key: <b>${hasApiKey() ? "set (is browser session me)" : "set nahi"}</b></p>` +
    `<p><input id="st-key" type="password" placeholder="API_KEY" autocomplete="off"> <button id="st-save">Save</button> <button id="st-clear">Clear</button></p>` +
    `<p><small>Key sirf is tab ke session me rehti hai, band karne par hat jaati hai. Production me HTTPS hi use karo.</small></p>`,
  ).then(() => {
    el.querySelector("#st-save")?.addEventListener("click", () => {
      const v = (el.querySelector("#st-key") as HTMLInputElement).value;
      if (v.trim()) setApiKey(v);
      location.hash = "#dashboard";
    });
    el.querySelector("#st-clear")?.addEventListener("click", () => {
      clearApiKey();
      location.reload();
    });
  });
}
