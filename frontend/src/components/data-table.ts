export function esc(v: unknown): string {
  const map: Record<string, string> = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
  return String(v).replace(/[&<>"']/g, (c) => map[c]);
}

/** Bharosemand HTML (jaise link) - table me bina escape ke jaata hai. Sirf apna banaya HTML do, API ka data nahi. */
export class Raw {
  constructor(public html: string) {}
}

export function renderTable(rows: Record<string, unknown>[]): string {
  if (!rows.length) return "<p>No data</p>";
  const cols = Object.keys(rows[0]);
  const head = cols.map((c) => `<th>${esc(c)}</th>`).join("");
  const cell = (v: unknown): string => (v instanceof Raw ? v.html : esc(v ?? ""));
  const body = rows.map((r) => `<tr>${cols.map((c) => `<td>${cell(r[c])}</td>`).join("")}</tr>`).join("");
  return `<div class="scroll"><table><tr>${head}</tr>${body}</table></div>`;
}

export function renderKeyValues(obj: Record<string, unknown>): string {
  return renderTable(Object.entries(obj).map(([key, value]) => ({ key, value: typeof value === "object" ? JSON.stringify(value) : value })));
}
