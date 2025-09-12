@'
from app.seed import generate_events
import json, urllib.request

def post(chunk):
    req = urllib.request.Request(
        "http://localhost:8000/events/bulk",
        data=json.dumps(chunk).encode(),
        headers={"Content-Type":"application/json"},
        method="POST",
    )
    print(urllib.request.urlopen(req).read().decode())

# Omaha + Miami (~6k total)
payload = []
payload += [e.model_dump(mode="json") for e in generate_events(3000, center=(41.2565,-95.9345))]
payload += [e.model_dump(mode="json") for e in generate_events(3000, center=(25.7617,-80.1918))]

# send in 2k chunks
for i in range(0, len(payload), 2000):
    post(payload[i:i+2000])
'@ | docker exec -i ngr001_api python -
