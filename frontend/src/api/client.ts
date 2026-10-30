const BASE: string = (globalThis as any).API_BASE ?? "http://localhost:8000";

export async function getJson<T>(path: string): Promise<T> {
  const r = await fetch(BASE + path);
  if (!r.ok) throw new Error(`GET ${path} failed: ${r.status}`);
  return (await r.json()) as T;
}

export async function postJson<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(BASE + path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  if (!r.ok) throw new Error(`POST ${path} failed: ${r.status}`);
  return (await r.json()) as T;
}
