export const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function fetchH3(params: Record<string,string|number>) {
  const qs = new URLSearchParams(params as any).toString();
  const res = await fetch(`${API}/aggregations/h3?${qs}`);
  return res.json();
}
