import { mountPage } from "../components/page";

export function render(el: HTMLElement): Promise<void> {
  return mountPage(el, "Create strategy", async () =>
    "<p>API se strategy banana abhi band hai (security: code isi process me chalta hai). Repo me <code>strategies/&lt;id&gt;/</code> banao: manifest.yaml + strategy.py, phir review karke commit.</p>");
}
