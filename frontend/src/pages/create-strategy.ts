import { mountPage, card } from "../components/page";

export function render(el: HTMLElement): Promise<void> {
  return mountPage(el, "Create strategy", async () => card(
    "<p>API से strategy बनाना अभी बंद है (security: code इसी प्रक्रिया में चलता है). रेपो में <code>strategies/&lt;id&gt;/</code> बनाएं: manifest.yaml + strategy.py, फिर समीक्षा करके commit करें.</p>"
  ));
}
