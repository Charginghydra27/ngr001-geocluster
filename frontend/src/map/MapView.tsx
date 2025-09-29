import React, { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import { MapboxOverlay } from "@deck.gl/mapbox";
import { H3HexagonLayer } from "@deck.gl/geo-layers";
import { fetchH3 } from "../api";
import "maplibre-gl/dist/maplibre-gl.css";

const CENTER: [number, number] = [-95.9345, 41.2565];

const MAPTILER_KEY = import.meta.env.VITE_MAPTILER_KEY as string | undefined;
const MAPTILER_STYLE =
  MAPTILER_KEY &&
  (`https://api.maptiler.com/maps/streets-v2/style.json?key=${MAPTILER_KEY}` as const);
const FALLBACK_STYLE = "https://demotiles.maplibre.org/style.json";

// helpers
const clamp = (n: number, min: number, max: number) =>
  Math.max(min, Math.min(max, n));

type BBox = { minx: number; miny: number; maxx: number; maxy: number; crosses: boolean };

function normalizedViewportBounds(map: maplibregl.Map): BBox {
  const b = map.getBounds();

  // Clamp to valid WGS84 ranges (use ±85 to avoid singularities near the poles)
  let minx = clamp(b.getWest(), -180, 180);
  let maxx = clamp(b.getEast(), -180, 180);
  const miny = clamp(b.getSouth(), -85, 85);
  const maxy = clamp(b.getNorth(), -85, 85);

  // If world wraps, east can be < west (crosses dateline)
  const crosses = maxx < minx;

  return { minx, miny, maxx, maxy, crosses };
}

export default function MapView() {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const overlayRef = useRef<MapboxOverlay | null>(null);
  const [res, setRes] = useState(7);

  useEffect(() => {
    if (!MAPTILER_KEY) {
      console.warn("[Map] Missing VITE_MAPTILER_KEY. Using fallback basemap.");
    }

    const map = new maplibregl.Map({
      container: containerRef.current!,
      style: MAPTILER_STYLE || FALLBACK_STYLE,
      center: CENTER,
      zoom: 9,
      attributionControl: false,
      renderWorldCopies: false, // ⬅️ stop duplicates outside [-180, 180]
      transformRequest: (url) => {
        if (url.includes("api.maptiler.com") && !url.includes("key=") && MAPTILER_KEY) {
          const sep = url.includes("?") ? "&" : "?";
          return { url: `${url}${sep}key=${MAPTILER_KEY}` };
        }
        return { url };
      },
    });

    map.on("error", (e) => console.error("[MapLibre error]", e?.error || e));

    map.addControl(
      new maplibregl.AttributionControl({
        compact: true,
        customAttribution: "© MapTiler © OpenStreetMap contributors",
      })
    );

    mapRef.current = map;

    // deck.gl overlay (works for v8/v9)
    const overlay = new MapboxOverlay({ interleaved: true, layers: [] });
    if (typeof (overlay as any).setMap === "function") {
      (overlay as any).setMap(map); // v8
    } else {
      map.addControl(overlay as unknown as maplibregl.IControl); // v9+
    }
    overlayRef.current = overlay;

    const paint = async () => {
      const { minx, miny, maxx, maxy, crosses } = normalizedViewportBounds(map);

      let data: any[] = [];
      try {
        if (crosses) {
          // Split across the anti-meridian and merge results
          const [left, right] = await Promise.all([
            fetchH3({ minx, miny, maxx: 180, maxy, res }),
            fetchH3({ minx: -180, miny, maxx, maxy, res }),
          ]);
          data = [...left, ...right];
        } else {
          data = await fetchH3({ minx, miny, maxx, maxy, res });
        }
      } catch (err) {
        console.error("[fetchH3 failed]", err);
        data = [];
      }

      overlay.setProps({
        layers: [
          new H3HexagonLayer({
            id: "h3-hexes",
            data,
            getHexagon: (d: any) => d.h3,
            getElevation: (d: any) => d.count,
            extruded: true,
            pickable: true,
          }),
        ],
      });
    };

    map.on("load", paint);
    map.on("moveend", paint);

    return () => {
      try {
        if (typeof (overlay as any).setMap === "function") {
          (overlay as any).setMap(null);
        } else {
          map.removeControl(overlay as unknown as maplibregl.IControl);
        }
      } catch {}
      overlay.finalize?.();
      map.remove();
    };
  }, []);

  // re-query on resolution change
  useEffect(() => {
    const map = mapRef.current;
    const overlay = overlayRef.current;
    if (!map || !overlay) return;

    (async () => {
      const { minx, miny, maxx, maxy, crosses } = normalizedViewportBounds(map);
      let data: any[] = [];
      try {
        if (crosses) {
          const [l, r] = await Promise.all([
            fetchH3({ minx, miny, maxx: 180, maxy, res }),
            fetchH3({ minx: -180, miny, maxx, maxy, res }),
          ]);
          data = [...l, ...r];
        } else {
          data = await fetchH3({ minx, miny, maxx, maxy, res });
        }
      } catch (e) {
        console.error("[fetchH3 failed]", e);
      }

      overlay.setProps({
        layers: [
          new H3HexagonLayer({
            id: "h3-hexes",
            data,
            getHexagon: (d: any) => d.h3,
            getElevation: (d: any) => d.count,
            extruded: true,
            pickable: true,
          }),
        ],
      });
    })();
  }, [res]);

  return (
    <div style={{ position: "relative", height: "100%" }}>
      <div ref={containerRef} style={{ position: "absolute", inset: 0 }} />
      <div
        style={{
          position: "absolute",
          top: 10,
          left: 10,
          background: "#fff",
          padding: 8,
          borderRadius: 8,
        }}
      >
        <label>H3 Res&nbsp;</label>
        <input
          type="range"
          min={5}
          max={9}
          value={res}
          onChange={(e) => setRes(parseInt(e.target.value, 10))}
        />
        <span style={{ marginLeft: 8 }}>{res}</span>
      </div>
    </div>
  );
}
