// API client. Production: API key sessionStorage se jaati hai (bundle me hardcode nahi).
// Base URL build-time env VITE_API_BASE se (docker build me /api). Dev me default localhost:8000.
const BASE: string = (import.meta as any).env?.VITE_API_BASE ?? "http://localhost:8000";
const KEY_NAME = "svl_api_key";

export function setApiKey(key: string): void {
  try {
    sessionStorage.setItem(KEY_NAME, key.trim());
  } catch {
    /* storage band ho to key sirf is page session me nahi rahegi */
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
  if (r.status === 401) throw new Error(`${label}: unauthorized (API key galat ya khaali)`);
  if (!r.ok) throw new Error(`${label} failed: ${r.status}`);
  return (await r.json()) as T;
}

export async function getJson<T>(path: string): Promise<T> {
  const r = await fetch(BASE + path, { headers: headers() });
  return handle<T>(r, `GET ${path}`);
}

export async function postJson<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(BASE + path, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
  });
  return handle<T>(r, `POST ${path}`);
}
