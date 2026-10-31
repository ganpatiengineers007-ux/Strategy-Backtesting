export function esc(v: unknown): string {
  const map: Record<string, string> = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
  return String(v).replace(/[&<>"']/g, (c) => map[c]);
}

export function renderTable(rows: Record<string, unknown>[]): string {
  if (!rows.length) return "<p>No data</p>";
  const cols = Object.keys(rows[0]);
  const head = cols.map((c) => `<th>${esc(c)}</th>`).join("");
  const body = rows.map((r) => `<tr>${cols.map((c) => `<td>${esc(r[c] ?? "")}</td>`).join("")}</tr>`).join("");
  return `<table><tr>${head}</tr>${body}</table>`;
}

export function renderKeyValues(obj: Record<string, unknown>): string {
  return renderTable(Object.entries(obj).map(([key, value]) => ({ key, value: typeof value === "object" ? JSON.stringify(value) : value })));
}
