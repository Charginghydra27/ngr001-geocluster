from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import Optional
from .db import get_db
from . import crud, schemas, clustering

app = FastAPI(title="NGR001 Geospatial API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/events/bulk")
def bulk(items: list[schemas.EventIn], db=Depends(get_db)):
    n = crud.bulk_insert_events(db, items)
    return {"inserted": n}

@app.get("/events")
def events(minx: float | None = None, miny: float | None = None,
          maxx: float | None = None, maxy: float | None = None,
          start: Optional[datetime] = None, end: Optional[datetime] = None,
          limit: int = 20000, db=Depends(get_db)):
    bbox = None
    if None not in (minx, miny, maxx, maxy):
        bbox = (minx, miny, maxx, maxy)
    rows = crud.query_events(db, bbox=bbox, start=start, end=end, limit=limit)
    return [schemas.EventOut.model_validate(r, from_attributes=True) for r in rows]

@app.get("/aggregations/h3")
def h3_agg(res: int = 7, minx: float | None = None, miny: float | None = None,
           maxx: float | None = None, maxy: float | None = None,
           start: Optional[datetime] = None, end: Optional[datetime] = None,
           limit: int = 200000, db=Depends(get_db)):
    bbox = None
    if None not in (minx, miny, maxx, maxy):
        bbox = (minx, miny, maxx, maxy)
    rows = crud.query_events(db, bbox=bbox, start=start, end=end, limit=limit)
    pts = [(r.lat, r.lon) for r in rows]
    bins = clustering.h3_bin(pts, res=res)
    return [{"h3": k, "count": v} for k, v in bins.items()]

@app.get("/clusters/dbscan")
def dbscan(eps_m: int = 500, min_samples: int = 5, minx: float | None = None, miny: float | None = None,
           maxx: float | None = None, maxy: float | None = None,
           start: Optional[datetime] = None, end: Optional[datetime] = None,
           limit: int = 20000, db=Depends(get_db)):
    bbox = None
    if None not in (minx, miny, maxx, maxy):
        bbox = (minx, miny, maxx, maxy)
    rows = crud.query_events(db, bbox=bbox, start=start, end=end, limit=limit)
    pts = [(r.lat, r.lon) for r in rows]
    labels = clustering.dbscan_haversine(pts, eps_m=eps_m, min_samples=min_samples)
    out = []
    for r, label in zip(rows, labels):
        out.append({"id": r.id, "lat": r.lat, "lon": r.lon, "label": int(label)})
    return out
