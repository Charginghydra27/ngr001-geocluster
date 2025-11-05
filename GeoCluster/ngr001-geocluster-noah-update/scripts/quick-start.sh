#!/bin/bash

set -e

echo "=========================================="
echo "GeoCluster Quick Start"
echo "=========================================="
echo ""

if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

echo "Step 1/3: Starting Docker services..."
docker compose up -d --build

echo ""
echo "Step 2/3: Waiting for services to start (30 seconds)..."
sleep 30

echo ""
echo "Checking API health..."
if curl -s http://localhost:8000/health | grep -q "ok"; then
    echo "✓ API is healthy"
else
    echo "✗ API is not responding. Check logs with: docker compose logs api"
    exit 1
fi

echo ""
echo "Step 3/3: Loading sample data (~6,000 events)..."
docker exec -i ngr001_api python - <<'EOF'
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

print("Generating events for Omaha, NE...")
payload = []
payload += [e.model_dump(mode="json") for e in generate_events(3000, center=(41.2565,-95.9345))]

print("Generating events for Miami, FL...")
payload += [e.model_dump(mode="json") for e in generate_events(3000, center=(25.7617,-80.1918))]

print("Uploading events to database...")
for i in range(0, len(payload), 2000):
    post(payload[i:i+2000])

print("Done! Loaded", len(payload), "events")
EOF

echo ""
echo "=========================================="
echo "✓ Setup complete!"
echo "=========================================="
echo ""
echo "Your geoclustering app is now running with sample data:"
echo ""
echo "  • Frontend: http://localhost:5173"
echo "  • API:      http://localhost:8000"
echo "  • API Docs: http://localhost:8000/docs"
echo ""
echo "To stop the services, run:"
echo "  docker compose down"
echo ""
echo "To view logs, run:"
echo "  docker compose logs -f"
echo ""
