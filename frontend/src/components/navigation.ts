const LINKS: [string, string][] = [["dashboard", "Dashboard"], ["strategies", "Strategies"], ["datasets", "Datasets"], ["runs", "Runs"],
  ["compare", "Compare"], ["health", "Health"], ["audit", "Audit"]];

export function navigation(): string {
  return LINKS.map(([h, l]) => `<a href="#${h}">${l}</a>`).join(" | ");
}
