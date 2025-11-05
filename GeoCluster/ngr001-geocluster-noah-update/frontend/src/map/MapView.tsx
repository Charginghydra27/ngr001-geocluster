import React, { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
// Deck.gl adapter that syncs Deck with (MapLibre) camera & WebGL context
import { MapboxOverlay } from "@deck.gl/mapbox";
// H3 visualization layer (each item = H3 cell with properties we map to height/color)
import { H3HexagonLayer } from "@deck.gl/geo-layers";
import { fetchH3 } from "../api";
import "maplibre-gl/dist/maplibre-gl.css";

// Omaha-ish center. initial view.
const CENTER: [number, number] = [-95.9345, 41.2565];

// describe the H3 aggregation shape we expect from the API
type H3Agg = { h3: string; count: number };

export default function MapView() {

  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const overlayRef = useRef<MapboxOverlay | null>(null);

  // H3 resolution state (5–9 are good interactive defaults)
  const [res, setRes] = useState(7);

  useEffect(() => {
    // 1) Spin up basemap
    const map = new maplibregl.Map({
      container: containerRef.current!,
      style: "https://demotiles.maplibre.org/style.json",
      center: CENTER,
      zoom: 9,
    });
    mapRef.current = map;

    // 2) Create deck.gl overlay.
    //    interleaved:true draws deck layers inside the same render pass as MapLibre (better perf)
    const overlay = new MapboxOverlay({ interleaved: true, layers: [] });
    // Attach as a MapLibre control (preferred pattern in current deck.gl)
    map.addControl(overlay as any);
    overlayRef.current = overlay;

    // Helper that fetches hex counts for current viewport and renders them
    const update = async () => {
      const b = map.getBounds(); // map’s current geographic viewport
      const data: H3Agg[] = await fetchH3({
        minx: b.getWest(),
        miny: b.getSouth(),
        maxx: b.getEast(),
        maxy: b.getNorth(),
        res,                    // <- H3 resolution slider value
      });

      overlay.setProps({
        layers: [
          new H3HexagonLayer({
            id: "h3-hexes",
            data,
            getHexagon: (d: H3Agg) => d.h3,
            getElevation: (d: H3Agg) => d.count,
            extruded: true,      // 3D columns
            pickable: true,      // enables hover/click interactivity later
            // getFillColor: (d: H3Agg) => [20, 120, 220, 160], // example solid color (RGBA)
          }),
        ],
      });
    };

    // 3) Load once and then on every camera settle
    map.on("load", update);
    map.on("moveend", update);

    // Cleanup: remove overlay control first, then the map
    return () => {
      if (overlayRef.current) map.removeControl(overlayRef.current as any);
      map.remove();
    };
  }, []); // run once

  /**
   * Re-run the aggregation when H3 resolution changes.
   * don’t need to rewire listeners—just fetch visible data at the new res and
   * replace the overlay’s layers.
   */
  useEffect(() => {
    const map = mapRef.current;
    const overlay = overlayRef.current;
    if (!map || !overlay) return;

    const b = map.getBounds();
    fetchH3({
      minx: b.getWest(),
      miny: b.getSouth(),
      maxx: b.getEast(),
      maxy: b.getNorth(),
      res,
    }).then((data: H3Agg[]) =>
      overlay.setProps({
        layers: [
          new H3HexagonLayer({
            id: "h3-hexes",
            data,
            getHexagon: (d: H3Agg) => d.h3,
            getElevation: (d: H3Agg) => d.count,
            extruded: true,
            pickable: true,
          }),
        ],
      })
    );
  }, [res]);

  return (
    <div style={{ position: "relative", height: "100%" }}>
      {/* Map container (MapLibre owns the canvas inside this div) */}
      <div ref={containerRef} style={{ position: "absolute", inset: 0 }} />

      {/* Minimal HUD for resolution control */}
      <div style={{ position: "absolute", top: 10, left: 10, background: "#fff", padding: 8, borderRadius: 8 }}>
        <label>H3 Res&nbsp;</label>
        <input
          type="range"
          min={5}
          max={9}
          value={res}
          onChange={(e) => setRes(parseInt(e.target.value))}
        />
        <span style={{ marginLeft: 8 }}>{res}</span>
      </div>
    </div>
  );
}
