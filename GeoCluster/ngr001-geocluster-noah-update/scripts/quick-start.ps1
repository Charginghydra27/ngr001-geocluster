# Quick start script to run the geoclustering app with sample data
# This script starts all services and loads sample data automatically

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "GeoCluster Quick Start" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
try {
    docker info | Out-Null
} catch {
    Write-Host "Error: Docker is not running. Please start Docker Desktop and try again." -ForegroundColor Red
    exit 1
}

# Start services
Write-Host "Step 1/3: Starting Docker services..." -ForegroundColor Yellow
docker compose up -d --build

# Wait for services to be ready
Write-Host ""
Write-Host "Step 2/3: Waiting for services to start (30 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Check if API is healthy
Write-Host ""
Write-Host "Checking API health..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
    if ($response.ok) {
        Write-Host "✓ API is healthy" -ForegroundColor Green
    }
} catch {
    Write-Host "✗ API is not responding. Check logs with: docker compose logs api" -ForegroundColor Red
    exit 1
}

# Load sample data
Write-Host ""
Write-Host "Step 3/3: Loading sample data (~6,000 events)..." -ForegroundColor Yellow

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

print("Generating events for Omaha, NE...")
payload = []
payload += [e.model_dump(mode="json") for e in generate_events(3000, center=(41.2565,-95.9345))]

print("Generating events for Miami, FL...")
payload += [e.model_dump(mode="json") for e in generate_events(3000, center=(25.7617,-80.1918))]

print("Uploading events to database...")
for i in range(0, len(payload), 2000):
    post(payload[i:i+2000])

print("Done! Loaded", len(payload), "events")
'@ | docker exec -i ngr001_api python -

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "✓ Setup complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Your geoclustering app is now running with sample data:"
Write-Host ""
Write-Host "  • Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "  • API:      http://localhost:8000" -ForegroundColor White
Write-Host "  • API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "To stop the services, run:"
Write-Host "  docker compose down" -ForegroundColor Gray
Write-Host ""
Write-Host "To view logs, run:"
Write-Host "  docker compose logs -f" -ForegroundColor Gray
Write-Host ""
