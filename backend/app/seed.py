from datetime import datetime, timedelta
import random
from .schemas import EventIn

TYPES = ["earthquake","power_outage","traffic","incident"]

def generate_events(n=2000, center=(41.2565,-95.9345)):
    lat0, lon0 = center
    now = datetime.utcnow()
    out = []
    for _ in range(n):
        lat = lat0 + random.uniform(-0.3, 0.3)
        lon = lon0 + random.uniform(-0.3, 0.3)
        t = now - timedelta(minutes=random.randint(0, 60*24*7))
        out.append(EventIn(occurred_at=t, lat=lat, lon=lon,
                           type=random.choice(TYPES),
                           severity=random.randint(1,5)))
    return out
