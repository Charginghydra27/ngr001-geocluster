const BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8000';

export async function fetchH3(params: {
  minx: number; miny: number; maxx: number; maxy: number; res: number;
}) {
  const qs = new URLSearchParams({
    minx: String(params.minx),
    miny: String(params.miny),
    maxx: String(params.maxx),
    maxy: String(params.maxy),
    res: String(params.res),
  });

  const url = `${BASE}/aggregations/h3?${qs.toString()}`;
  const r = await fetch(url);
  if (!r.ok) {
    const body = await r.text().catch(() => '');
    console.error('[fetchH3 error]', r.status, body);
    throw new Error(`fetchH3 ${r.status}`);
  }
  return r.json();
}
