from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Iterable
from collections import Counter

from fastapi import FastAPI, Depends, Request, Query
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="NGR001 Geospatial API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400,
)

from .db import get_db
from . import crud, schemas, clustering

# ---------------- helpers ----------------

def _clamp_bbox(minx: float, miny: float, maxx: float, maxy: float):
    minx = max(-180.0, min(180.0, float(minx)))
    maxx = max(-180.0, min(180.0, float(maxx)))
    miny = max(-85.0,  min(85.0,  float(miny)))
    maxy = max(-85.0,  min(85.0,  float(maxy)))
    return minx, miny, maxx, maxy


def _split_bbox(minx: float, miny: float, maxx: float, maxy: float):
    minx, miny, maxx, maxy = _clamp_bbox(minx, miny, maxx, maxy)
    crosses = (maxx < minx) or ((maxx - minx) > 180.0)
    if crosses:
        return [(minx, miny, 180.0, maxy), (-180.0, miny, maxx, maxy)]
    return [(minx, miny, maxx, maxy)]


def _combine_sources(request: Request, include_qs: List[str], sources_csv: Optional[str]) -> List[str]:
    """
    Accept either:
      - repeated keys:   ?include=demo&include=us_accidents
      - comma list:      ?sources=demo,us_accidents
    """
    include_list = list(include_qs or [])
    # also support ?include= repeated captured via Request if needed
    include_list.extend(request.query_params.getlist("include"))
    if sources_csv:
        include_list.extend(s.strip() for s in sources_csv.split(",") if s.strip())
    # de-dup while preserving order
    seen, out = set(), []
    for s in include_list:
        if s and s not in seen:
            seen.add(s)
            out.append(s)
    return out


# ---------------- routes ----------------

@app.get("/health")
def health():
    return {"ok": True}


@app.post("/events/bulk")
def bulk(items: List[schemas.EventIn], db=Depends(get_db)):
    n = crud.bulk_insert_events(db, items)
    return {"inserted": n}

@app.patch("/events/bulk_update")
def update_event(items: List[schemas.EventUpdate], db=Depends(get_db)):
    updated = crud.bulk_update_events(db, items)
    return {"updated": updated}

@app.get("/events")
def events(
    request: Request,
    minx: float | None = None, miny: float | None = None,
    maxx: float | None = None, maxy: float | None = None,
    start: Optional[datetime] = None, end: Optional[datetime] = None,
    include: List[str] = Query(default=[]),
    sources: Optional[str] = None,
    limit: int = 20_000,
    db=Depends(get_db),
):
    selected = _combine_sources(request, include, sources)

    if None in (minx, miny, maxx, maxy):
        rows = crud.query_events(db, bbox=None, start=start, end=end, limit=limit, sources=selected)
        return [schemas.EventOut.model_validate(r, from_attributes=True) for r in rows]

    out: list = []
    for bbox in _split_bbox(minx, miny, maxx, maxy):
        out.extend(crud.query_events(db, bbox=bbox, start=start, end=end, limit=limit, sources=selected))

    out = out[:limit]
    return [schemas.EventOut.model_validate(r, from_attributes=True) for r in out]

@app.get("/aggregations/h3")
def h3_agg(
    request: Request,
    res: int = 7,
    minx: float | None = None, miny: float | None = None,
    maxx: float | None = None, maxy: float | None = None,
    start: Optional[datetime] = None, end: Optional[datetime] = None,
    include: List[str] = Query(default=[]),
    sources: Optional[str] = None,
    limit: int = 200_000,
    db=Depends(get_db),
):
    selected = _combine_sources(request, include, sources)

    parts: list[tuple[float, float, float, float]]
    if None in (minx, miny, maxx, maxy):
        parts = [(None, None, None, None)]
    else:
        parts = _split_bbox(minx, miny, maxx, maxy)

    bins = Counter()
    for p in parts:
        bbox = None if p[0] is None else p
        rows = crud.query_events(db, bbox=bbox, start=start, end=end, limit=limit, sources=selected)
        pts = [(r.lat, r.lon) for r in rows]
        if pts:
            bins.update(clustering.h3_bin(pts, res=res))

    return [{"h3": h, "count": int(c)} for h, c in bins.items()]


@app.get("/clusters/dbscan")
def dbscan(
    request: Request,
    eps_m: int = 500, min_samples: int = 5,
    minx: float | None = None, miny: float | None = None,
    maxx: float | None = None, maxy: float | None = None,
    start: Optional[datetime] = None, end: Optional[datetime] = None,
    include: List[str] = Query(default=[]),
    sources: Optional[str] = None,
    limit: int = 20_000,
    db=Depends(get_db),
):
    selected = _combine_sources(request, include, sources)

    bbox = None
    if None not in (minx, miny, maxx, maxy):
        bbox = (minx, miny, maxx, maxy)

    rows = crud.query_events(db, bbox=bbox, start=start, end=end, limit=limit, sources=selected)
    pts = [(r.lat, r.lon) for r in rows]
    labels = clustering.dbscan_haversine(pts, eps_m=eps_m, min_samples=min_samples)
    return [{"id": r.id, "lat": r.lat, "lon": r.lon, "label": int(label)} for r, label in zip(rows, labels)]
