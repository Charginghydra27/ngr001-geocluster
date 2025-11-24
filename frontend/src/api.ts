import { API_BASE } from "./config"
import {hexToBox} from "./utils/h3"
export const API = API_BASE;

export async function fetchEventsInHex(h3: string, sources: string[]) {
  //Get the parameters for the API call
  const {minx, miny, maxx, maxy} = hexToBox(h3);
  const qs = new URLSearchParams({
    minx: String(minx),
    miny: String(miny),
    maxx: String(maxx),
    maxy: String(maxy),
    limit: "10000"
  });
  for (const src of sources) {
    qs.append("include", src);
  }

  //Get the url from the parameters
  const url = `${API}/events?${qs.toString()}`;
  
  //Fetch
  try {
    const r = await fetch(url, { headers: { Accept: "application/json" } });
    if(!r.ok) throw new Error(`HTTP ${r.status}`);
    return await r.json();
  } catch (e) {
    console.error("fetchEventsInHex failed:", url, e);
    return [];
  }
}

export async function fetchH3(params: Record<string, string | number | string[]>) {
  const qs = new URLSearchParams();
  let sourcesComma = "";

  for (const [k, v] of Object.entries(params)) {
    if (Array.isArray(v)) {
      v.forEach((val) => qs.append(k, String(val))); // include=a&include=b...
      if (k === "include") sourcesComma = v.join(",");
    } else if (v !== undefined && v !== null) {
      qs.set(k, String(v));
      if (k === "sources") sourcesComma = String(v);
    }
  }
  if (sourcesComma && !qs.has("sources")) qs.set("sources", sourcesComma);

  const url = `${API}/aggregations/h3?${qs.toString()}`;
  try {
    const r = await fetch(url, { headers: { Accept: "application/json" } });
    if (!r.ok) throw new Error(`HTTP ${r.status} ${r.statusText}`);
    const json = await r.json();
    if (!Array.isArray(json)) throw new Error("Expected array JSON");
    return json as Array<{ h3: string; count: number }>;
  } catch (e) {
    console.error("fetchH3 failed:", url, e);
    return [];
  }
}
