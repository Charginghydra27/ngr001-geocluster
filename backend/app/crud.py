from __future__ import annotations
from typing import Iterable, Optional, Tuple, List
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import text

from . import models, schemas

BBox = Tuple[float, float, float, float]


def bulk_insert_events(db: Session, items: List[schemas.EventIn]) -> int:
    objs = [models.Event(**i.model_dump()) for i in items]
    db.add_all(objs)
    db.commit()
    return len(objs)


def _as_array_param(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(v for v in values if v))


def query_events(
    db: Session,
    *,
    bbox: Optional[BBox] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    limit: int = 20000,
    sources: Optional[Iterable[str]] = None,
):
    start = start or datetime.min
    end = end or datetime.max
    src_list = _as_array_param(sources or [])

    # base SQL + params
    if bbox:
        minx, miny, maxx, maxy = bbox
        sql = (
            "SELECT * FROM events "
            "WHERE occurred_at >= :start AND occurred_at < :end "
            "AND ST_Intersects(geom::geometry, ST_MakeEnvelope(:minx,:miny,:maxx,:maxy,4326)) "
        )
        params = {
            "start": start, "end": end,
            "minx": minx, "miny": miny, "maxx": maxx, "maxy": maxy,
            "limit": limit,
        }
    else:
        sql = (
            "SELECT * FROM events "
            "WHERE occurred_at >= :start AND occurred_at < :end "
        )
        params = {"start": start, "end": end, "limit": limit}

    # source filter: JSON 'source' OR 'type = demo' for simulated points
    if src_list:
        want_demo = "demo" in {s.lower() for s in src_list}
        if want_demo:
            sql += "AND (properties->>'source' = ANY(:sources) OR type = 'demo') "
        else:
            sql += "AND properties->>'source' = ANY(:sources) "
        params["sources"] = src_list

    sql += "LIMIT :limit"

    q = db.query(models.Event).from_statement(text(sql).bindparams(**params))
    return q.all()
