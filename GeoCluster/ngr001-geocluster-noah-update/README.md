# NGR001 — Real-Time Geospatial Event Clustering

This project aims to ingest geospatial “events”, store them in **PostGIS**, and serve **H3 hexagon aggregations** to a **React + MapLibre GL + deck.gl** UI.

---

## Contents
- [Stack](#stack) • [Architecture](#architecture) • [Prerequisites](#prerequisites)  
- [Quickstart](#quickstart-25-min) • [Structure](#Structure) • [Dev workflow](#dev-workflow) 





---

## Stack
**Backend**: Python **FastAPI**, PostgreSQL **PostGIS**, SQLAlchemy 2.x  
**Frontend**: **Vite** + **React** + **TypeScript**, **MapLibre GL**, **deck.gl** `H3HexagonLayer`  
**Ops**: **Docker Compose** (PostGIS + API); seed helpers (**PowerShell** / **bash**)

---

## Architecture
- `db/` → Postgres init with PostGIS.
- `backend/` → FastAPI routes:
  - `GET /events` (sample page)
  - `POST /events/bulk` (seed helper)
  - `GET /aggregations/h3` (server-side H3 counts by viewport)
- `frontend/` → Vite/React map with deck.gl overlay (via `MapboxOverlay`).

Ports: **API** `http://localhost:8000` • **DB** `localhost:5432` • **UI** `http://localhost:5173`

---

## Prerequisites
- **Docker Desktop** (Windows: enable WSL2)
- **Node.js 22+** for the dev UI
  - **Windows (recommended via nvm)**
    ```powershell
    winget install CoreyButler.NVMforWindows
    nvm install 22.12.0
    nvm use 22.12.0
    ```
  - **macOS/Linux (nvm)**
    ```bash
    nvm install 22 && nvm use 22
    ```
- **Windows first run only** – allow local scripts:
  ```powershell
  Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

## Quickstart (2–5 min)

### Option 1: Quick Start (Recommended - One Command)

Run everything with sample data automatically loaded:

**macOS/Linux:**
```bash
git clone https://github.com/Carroy3443/GeoCluster.git
cd GeoCluster/ngr001-geocluster-noah-update
./scripts/quick-start.sh
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/Carroy3443/GeoCluster.git
cd GeoCluster\ngr001-geocluster-noah-update
.\scripts\quick-start.ps1
```

This will:
- Start all Docker services (database, API, frontend)
- Load ~6,000 sample events (Omaha, NE and Miami, FL)
- Open the app at http://localhost:5173

**Important:** You need a MapTiler API key for the map to display. Get a free key at https://www.maptiler.com/cloud/ and create a `.env` file:
```bash
echo "VITE_MAPTILER_KEY=your_key_here" > .env
```
Then restart: `docker compose up -d --build`

### Option 2: Manual Setup

1) **Clone**
```bash
git clone https://github.com/Carroy3443/GeoCluster.git
cd GeoCluster/ngr001-geocluster-noah-update
```

2) **Start DB + API**
```bash
docker compose up -d --build
curl http://localhost:8000/health   # -> {"ok":true}
# API docs: http://localhost:8000/docs
```

3) **Seed data**
```bash
.\scripts\seed.ps1
```

4) **Load external weather databases (optional)**
The system includes integration with two external weather databases that supplement the manual data:
- NOAA Severe Weather Data Inventory (hail events)
- US Weather Events (2016-2022)

To load these databases:
```bash
# Load all records (may take significant time)
.\scripts\load_external_data.ps1

# Or load a limited number for testing (e.g., 10000 records per database)
.\scripts\load_external_data.ps1 10000
```

For Linux/macOS:
```bash
./scripts/load_external_data.sh
# Or with limit:
./scripts/load_external_data.sh 10000
```

5) **Run the UI**
```bash
cd frontend
# if present:
[ -f .env.example ] && cp .env.example .env
npm ci
npm run dev
# open http://localhost:5173
```

**Note**: The external weather databases (step 4) supplement the manual seed data (step 3). Both can coexist in the system, and you can use either or both data sources.



## Structure ##
```bash
├─ backend/
│  ├─ app/
│  │  ├─ main.py          # FastAPI entry
│  │  ├─ models.py        # SQLAlchemy models (PostGIS columns)
│  │  ├─ schemas.py       # Pydantic I/O models
│  │  ├─ crud.py          # DB access helpers
│  │  ├─ clustering.py    # server-side H3 aggregation
│  │  └─ seed.py          # synthetic event generator
│  └─ requirements.txt
├─ db/
│  └─ init.sql            # enables PostGIS, base schema
├─ frontend/
│  ├─ src/
│  │  ├─ api.ts           # small fetch helpers
│  │  ├─ map/MapView.tsx  # MapLibre + deck.gl overlay
│  │  ├─ App.tsx
│  │  └─ ...
│  └─ vite.config.ts
├─ scripts/
│  ├─ seed.ps1            # Windows seeder
│  └─ seed.sh             # macOS/Linux seeder (optional)
├─ docker-compose.yml     # PostGIS + FastAPI
└─ README.md
```


## dev-workflow ##
1) **Branching**
2) **Run services locally**
3) **Commit & PR**
4) **Keep docs up-to-date**






