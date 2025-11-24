import React, { useEffect, useMemo, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import { MapboxOverlay } from "@deck.gl/mapbox";
import { H3HexagonLayer } from "@deck.gl/geo-layers";
import { fetchEventsInHex, fetchH3 } from "../api";
import { MAPTILER_KEY } from "../config";
import "maplibre-gl/dist/maplibre-gl.css";
import HexEventTable from "./TableView";

type H3Agg = { h3: string; count: number };
const CENTER: [number, number] = [-95.9345, 41.2565];

// Must match properties->>'source' in DB
const DATASETS = [
  { id: "demo",                label: "Demo (simulated)" },
  { id: "noaa_severe_weather", label: "NOAA Hail" },
  { id: "us_weather_events",   label: "US Weather Events" },
  { id: "us_accidents",        label: "US Accidents" },
] as const;

export default function MapView() {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const overlayRef = useRef<MapboxOverlay | null>(null);

  // UI state
  const [res, setRes] = useState(5);
  const [selected, setSelected] = useState<Record<string, boolean>>(
    () => Object.fromEntries(DATASETS.map(d => [d.id, true]))
  );

  //Clicked tile and events
  const [activeHex, setActiveHex] = useState<string | null>(null);
  const [hexEvents, setHexEvents] = useState<any[] | null>(null);

  // Derived selection + refs so handlers always see fresh values
  const selectedIds = useMemo(
    () => DATASETS.filter(d => selected[d.id]).map(d => d.id),
    [selected]
  );
  const selectedIdsRef = useRef<string[]>(selectedIds);
  useEffect(() => { selectedIdsRef.current = selectedIds; }, [selectedIds]);

  const resRef = useRef<number>(res);
  useEffect(() => { resRef.current = res; }, [res]);

  // Single fetch+render function that ONLY reads from refs (fresh values)
  const requestAndRender = async () => {
    const map = mapRef.current;
    const overlay = overlayRef.current;
    if (!map || !overlay) return;

    const ids = selectedIdsRef.current;
    if (ids.length === 0) {
      overlay.setProps({ layers: [] });
      return;
    }

    const b = map.getBounds();
    const params = {
      minx: b.getWest(),
      miny: b.getSouth(),
      maxx: b.getEast(),
      maxy: b.getNorth(),
      res: resRef.current,
      include: ids,            // repeated keys
      sources: ids.join(","),  // comma string (fallback)
    };

    const data: H3Agg[] = await fetchH3(params);

    overlay.setProps({
      layers: [
        new H3HexagonLayer({
          id: "h3-hexes",
          data,
          getHexagon: (d: H3Agg) => d.h3,
          getElevation: (d: H3Agg) => d.count,
          elevationScale: 20,
          extruded: true,
          pickable: true,
          getFillColor: (d: H3Agg) => [20, 120, 220, 180],
          wrapLongitude: false,

          onClick: (info, event) => {
            if (!info.object) return;

            const hex = info.object.h3

            setActiveHex(hex);
            setHexEvents(null);
            
            void (async () => {
              const events = await fetchEventsInHex(hex, selectedIdsRef.current);
              console.log("Fetched Events:", events)
              setHexEvents(events);
            })();

          }
        }),
      ],
    });
  };

  // Init map + overlay once; handlers call the ref-driven function above
  useEffect(() => {
    const map = new maplibregl.Map({
      container: containerRef.current!,
      style: `https://api.maptiler.com/maps/streets-v2/style.json?key=${MAPTILER_KEY}`,
      center: CENTER,
      zoom: 5,
      renderWorldCopies: false,
    });
    mapRef.current = map;

    const overlay = new MapboxOverlay({ interleaved: true, layers: [] });
    map.addControl(overlay as any);
    overlayRef.current = overlay;

    const handler = () => { void requestAndRender(); };
    map.on("load", handler);
    map.on("moveend", handler);

    return () => {
      if (overlayRef.current) map.removeControl(overlayRef.current as any);
      map.remove();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Re-query when the UI state changes
  useEffect(() => { void requestAndRender(); }, [res, selectedIds.join("|")]);

  const toggle = (id: string) => setSelected((p) => ({ ...p, [id]: !p[id] }));

  return (
    <div style={{ position: "relative", height: "100%" }}>
      <div ref={containerRef} style={{ position: "absolute", inset: 0 }} />
      <div
        style={{
          position: "absolute",
          top: 10,
          left: 10,
          background: "#111a",
          color: "#fff",
          padding: 10,
          borderRadius: 8,
          width: 190,
        }}
      >
        <div style={{ fontWeight: 700, marginBottom: 6 }}>H3 Resolution</div>
        <input
          type="range"
          min={5}
          max={9}
          value={res}
          onChange={(e) => setRes(parseInt(e.target.value))}
          style={{ width: "100%" }}
        />
        <div style={{ fontSize: 12, marginTop: 4 }}>{res}</div>

        <div style={{ marginTop: 12, fontWeight: 700 }}>
          Datasets (show when checked)
        </div>
        <div style={{ marginTop: 6 }}>
          {DATASETS.map(d => (
            <label key={d.id} style={{ display: "block", fontSize: 13 }}>
              <input
                type="checkbox"
                checked={!!selected[d.id]}
                onChange={() => toggle(d.id)}
                style={{ marginRight: 6 }}
              />
              {d.label}
            </label>
          ))}
        </div>
      </div>

      <HexEventTable activeHex={activeHex} hexEvents={hexEvents} onClose={() => setActiveHex(null)} />
    </div>

  );
}
