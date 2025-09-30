import { API_BASE } from "./config";
export const API = API_BASE;

export async function fetchH3(params: Record<string, string | number>) {
  const qs = new URLSearchParams(params as any).toString();
  const url = `${API}/aggregations/h3?${qs}`;
  try {
    const r = await fetch(url, { headers: { Accept: "application/json" } });
    if (!r.ok) {
      const text = await r.text().catch(() => "");
      throw new Error(`HTTP ${r.status} ${r.statusText} – ${text}`);
    }
    const json = await r.json();
    if (!Array.isArray(json)) throw new Error("Expected array JSON");
    return json as Array<{ h3: string; count: number }>;
  } catch (e) {
    console.error("fetchH3 failed:", url, e);
    return []; // never undefined
  }
}
