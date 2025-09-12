# Seed Instructions

Inside the running API container, run a small Python snippet to generate and insert synthetic events.

```bash
docker exec -it ngr001_api python - <<'PY'
from app.seed import generate_events
import requests
items=[e.model_dump() for e in generate_events(4000)]
print(requests.post('http://localhost:8000/events/bulk', json=items[:2000]).json())
print(requests.post('http://localhost:8000/events/bulk', json=items[2000:]).json())
PY
```
