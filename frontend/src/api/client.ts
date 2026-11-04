// API client. API key sessionStorage se jaati hai (bundle me hardcode nahi).
// Base URL build-time env VITE_API_BASE se (docker me /api). Dev me default localhost:8000.
const BASE: string = (import.meta as any).env?.VITE_API_BASE ?? "http://localhost:8000";
const KEY_NAME = "svl_api_key";

export function setApiKey(key: string): void {
  try {
    sessionStorage.setItem(KEY_NAME, key.trim());
  } catch {
    /* storage band ho to key sirf is page session me nahi rahegi */
  }
}

export function clearApiKey(): void {
  try {
    sessionStorage.removeItem(KEY_NAME);
  } catch {
    /* ignore */
  }
}

export function hasApiKey(): boolean {
  try {
    return !!sessionStorage.getItem(KEY_NAME);
  } catch {
    return false;
  }
}

function headers(extra: Record<string, string> = {}): Record<string, string> {
  const h: Record<string, string> = { ...extra };
  try {
    const k = sessionStorage.getItem(KEY_NAME);
    if (k) h["X-API-Key"] = k;
  } catch {
    /* ignore */
  }
  return h;
}

async function handle<T>(r: Response, label: string): Promise<T> {
  if (r.status === 401) throw new Error(`${label}: unauthorized (Settings me API key daalo)`);
  if (!r.ok) {
    let detail = "";
    try {
      const body = await r.json();
      detail = typeof body?.detail === "string" ? body.detail : JSON.stringify(body?.detail ?? body);
    } catch {
      detail = "";
    }
    const rid = r.headers.get("X-Request-ID");
    throw new Error(`${label} failed: ${r.status}${detail ? ` - ${detail}` : ""}${rid ? ` (request ${rid})` : ""}`);
  }
  return (await r.json()) as T;
}

export async function getJson<T>(path: string): Promise<T> {
  return handle<T>(await fetch(BASE + path, { headers: headers() }), `GET ${path}`);
}

export async function postJson<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(BASE + path, { method: "POST", headers: headers({ "Content-Type": "application/json" }), body: JSON.stringify(body) });
  return handle<T>(r, `POST ${path}`);
}
