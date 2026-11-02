const LINKS: [string, string][] = [["dashboard", "Dashboard"], ["live", "Live"], ["new-run", "New run"], ["runs", "Runs"], ["strategies", "Strategies"],
  ["datasets", "Datasets"], ["compare", "Compare"], ["health", "Health"], ["audit", "Audit"], ["settings", "Settings"]];

export function navigation(): string {
  return LINKS.map(([h, l]) => `<a href="#${h}">${l}</a>`).join("");
}
