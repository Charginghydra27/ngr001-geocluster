from sqlalchemy.orm import Session
from sqlalchemy import text
from . import models, schemas
from datetime import datetime

def bulk_insert_events(db: Session, items: list[schemas.EventIn]) -> int:
    objs = [models.Event(**i.model_dump()) for i in items]
    db.add_all(objs)
    db.commit()
    return len(objs)

def query_events(db: Session, *, bbox=None, start=None, end=None, limit=20000):
    q = db.query(models.Event)
    if start:
        q = q.filter(models.Event.occurred_at >= start)
    if end:
        q = q.filter(models.Event.occurred_at < end)
    if bbox:
        minx, miny, maxx, maxy = bbox
        q = q.from_statement(text(
            "SELECT * FROM events "
            "WHERE occurred_at >= :start AND occurred_at < :end "
            "AND ST_Intersects(geom::geometry, ST_MakeEnvelope(:minx,:miny,:maxx,:maxy,4326)) "
            "LIMIT :limit"
        ).params(start=start or datetime.min, end=end or datetime.max,
                 minx=minx, miny=miny, maxx=maxx, maxy=maxy, limit=limit))
    else:
        q = q.limit(limit)
    return q.all()
