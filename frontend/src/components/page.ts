import { errorPanel } from "./error-panel";
import { esc } from "./data-table";

export async function mountPage(el: HTMLElement, title: string, loader: () => Promise<string>): Promise<void> {
  const h = `<h2>${esc(title)}</h2>`;
  el.innerHTML = h + "<p>Loading...</p>";
  try {
    el.innerHTML = h + (await loader());
  } catch (e) {
    el.innerHTML = h + errorPanel(String(e));
  }
}
