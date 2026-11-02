import { errorPanel } from "./error-panel";
import { esc } from "./data-table";

const leaveFns: (() => void)[] = [];

/** Page chhodte waqt (timer band karne jaise) kaam. */
export function onLeave(fn: () => void): void {
  leaveFns.push(fn);
}

export function runLeave(): void {
  while (leaveFns.length) (leaveFns.pop() as () => void)();
}

export async function mountPage(el: HTMLElement, title: string, loader: () => Promise<string>): Promise<void> {
  const h = `<h2>${esc(title)}</h2>`;
  el.innerHTML = h + "<p>Loading...</p>";
  try {
    el.innerHTML = h + (await loader());
  } catch (e) {
    el.innerHTML = h + errorPanel(String(e));
  }
}
