import React, { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import { MapboxOverlay } from "@deck.gl/mapbox";
import { H3HexagonLayer } from "@deck.gl/geo-layers";
import { fetchH3 } from "../api";
import { MAPTILER_KEY } from "../config";
import "maplibre-gl/dist/maplibre-gl.css";

const CENTER: [number, number] = [-95.9345, 41.2565];
type H3Agg = { h3: string; count: number };

export default function MapView() {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const overlayRef = useRef<MapboxOverlay | null>(null);
  const [res, setRes] = useState(7);

  useEffect(() => {
    const map = new maplibregl.Map({
      container: containerRef.current!,
      style: `https://api.maptiler.com/maps/streets-v2/style.json?key=${MAPTILER_KEY}`,
      center: CENTER,
      zoom: 9,
      renderWorldCopies: false, // ⟵ no multi-world wrapping
      // maxBounds: [[-130, 20], [-60, 55]], // (optional: keep users in the US)
    });
    mapRef.current = map;

    const overlay = new MapboxOverlay({ interleaved: true, layers: [] });
    map.addControl(overlay as any);
    overlayRef.current = overlay;

    const update = async () => {
      const b = map.getBounds();
      const params = {
        minx: b.getWest(),
        miny: b.getSouth(),
        maxx: b.getEast(),
        maxy: b.getNorth(),
        res,
      };
      const data: H3Agg[] = await fetchH3(params);
      console.log("H3 cells length:", data.length, data[0]);

      overlay.setProps({
        layers: [
          new H3HexagonLayer({
            id: "h3-hexes",
            data,
            getHexagon: (d: H3Agg) => d.h3,
            getElevation: (d: H3Agg) => d.count,
            elevationScale: 20,                         // ⟵ taller columns
            extruded: true,
            pickable: true,
            getFillColor: (d: H3Agg) => [20, 120, 220, 180], // ⟵ visible color
            wrapLongitude: false,                       // ⟵ avoid antimeridian dupes
          }),
        ],
      });
    };

    map.on("load", update);
    map.on("moveend", update);

    return () => {
      if (overlayRef.current) map.removeControl(overlayRef.current as any);
      map.remove();
    };
  }, []);

  // Re-query when resolution changes
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
            elevationScale: 20,
            extruded: true,
            pickable: true,
            getFillColor: (d: H3Agg) => [20, 120, 220, 180],
            wrapLongitude: false,
          }),
        ],
      })
    );
  }, [res]);

  return (
    <div style={{ position: "relative", height: "100%" }}>
      <div ref={containerRef} style={{ position: "absolute", inset: 0 }} />
      <div style={{ position: "absolute", top: 10, left: 10, background: "#fff", padding: 8, borderRadius: 8 }}>
        <label>H3 Res&nbsp;</label>
        <input type="range" min={5} max={9} value={res} onChange={(e) => setRes(parseInt(e.target.value))} />
        <span style={{ marginLeft: 8 }}>{res}</span>
      </div>
    </div>
  );
}
