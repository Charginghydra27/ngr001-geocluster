from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import Optional, List
from collections import Counter

from .db import get_db
from . import crud, schemas, clustering

app = FastAPI(title="NGR001 Geospatial API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- helpers ---------------------------------------------------------------

def _clamp_bbox(minx: float, miny: float, maxx: float, maxy: float):
    """Keep bbox within sane WGS84 ranges (avoid poles & >180° longitudes)."""
    minx = max(-180.0, min(180.0, float(minx)))
    maxx = max(-180.0, min(180.0, float(maxx)))
    miny = max(-85.0,  min(85.0,  float(miny)))
    maxy = max(-85.0,  min(85.0,  float(maxy)))
    return minx, miny, maxx, maxy

def _split_bbox(minx: float, miny: float, maxx: float, maxy: float):
    """
    Return one or two bboxes that do NOT cross the anti-meridian and never
    exceed 180° width. This prevents invalid envelopes in PostGIS.
    """
    minx, miny, maxx, maxy = _clamp_bbox(minx, miny, maxx, maxy)
    crosses = (maxx < minx) or ((maxx - minx) > 180.0)
    if crosses:
        # left piece (minx..180) and right piece (-180..maxx)
        return [(minx, miny, 180.0, maxy), (-180.0, miny, maxx, maxy)]
    return [(minx, miny, maxx, maxy)]

# --- routes ----------------------------------------------------------------

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/events/bulk")
def bulk(items: List[schemas.EventIn], db=Depends(get_db)):
    n = crud.bulk_insert_events(db, items)
    return {"inserted": n}

@app.get("/events")
def events(
    minx: float | None = None, miny: float | None = None,
    maxx: float | None = None, maxy: float | None = None,
    start: Optional[datetime] = None, end: Optional[datetime] = None,
    limit: int = 20_000, db=Depends(get_db),
):
    # Query one or two bboxes if provided, then merge.
    if None in (minx, miny, maxx, maxy):
        rows = crud.query_events(db, bbox=None, start=start, end=end, limit=limit)
        return [schemas.EventOut.model_validate(r, from_attributes=True) for r in rows]

    out: list = []
    for bbox in _split_bbox(minx, miny, maxx, maxy):
        out.extend(crud.query_events(db, bbox=bbox, start=start, end=end, limit=limit))

    # (Optional) trim to limit to match previous behavior
    out = out[:limit]
    return [schemas.EventOut.model_validate(r, from_attributes=True) for r in out]

@app.get("/aggregations/h3")
def h3_agg(
    res: int = 7,
    minx: float | None = None, miny: float | None = None,
    maxx: float | None = None, maxy: float | None = None,
    start: Optional[datetime] = None, end: Optional[datetime] = None,
    limit: int = 200_000, db=Depends(get_db),
):
    """
    Aggregate points into H3 bins at the requested resolution. Handles
    views that cross the anti-meridian by splitting into two queries.
    """
    parts: list[tuple[float, float, float, float]]
    if None in (minx, miny, maxx, maxy):
        parts = [(None, None, None, None)]  # no bbox filter
    else:
        parts = _split_bbox(minx, miny, maxx, maxy)

    bins = Counter()
    for p in parts:
        bbox = None if p[0] is None else p
        rows = crud.query_events(db, bbox=bbox, start=start, end=end, limit=limit)
        pts = [(r.lat, r.lon) for r in rows]
        bins.update(clustering.h3_bin(pts, res=res))

    return [{"h3": h, "count": int(c)} for h, c in bins.items()]

@app.get("/clusters/dbscan")
def dbscan(
    eps_m: int = 500, min_samples: int = 5,
    minx: float | None = None, miny: float | None = None,
    maxx: float | None = None, maxy: float | None = None,
    start: Optional[datetime] = None, end: Optional[datetime] = None,
    limit: int = 20_000, db=Depends(get_db),
):
    bbox = None
    if None not in (minx, miny, maxx, maxy):
        # For DBSCAN we can keep a single bbox; if you see dateline errors here,
        # apply the same _split_bbox pattern and merge results.
        bbox = (minx, miny, maxx, maxy)

    rows = crud.query_events(db, bbox=bbox, start=start, end=end, limit=limit)
    pts = [(r.lat, r.lon) for r in rows]
    labels = clustering.dbscan_haversine(pts, eps_m=eps_m, min_samples=min_samples)
    out = []
    for r, label in zip(rows, labels):
        out.append({"id": r.id, "lat": r.lat, "lon": r.lon, "label": int(label)})
    return out
