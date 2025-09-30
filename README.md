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


---
## Quickstart 

1) **Clone**
```bash
git clone https://github.com/Charginghydra27/ngr001-geocluster.git
cd ngr001-geocluster
```

2) **Start DB + API + UI (Docker)**
```bash
docker compose up -d --build
# API health: http://localhost:8000/health   -> {"ok": true}
# API docs:   http://localhost:8000/docs
# Frontend:   http://localhost:5173
```

3) **Seed data (Omaha Clustered Events)**

**Windows Powershell / CMD**
```bash
docker compose exec db psql -U postgres -d eventsdb -c "INSERT INTO events (occurred_at, lat, lon, type, severity) SELECT NOW() - (random() * interval '30 days'), 41.0 + random()*1.5, -96.6 + random()*2.0, 'demo', (floor(random()*5))::int FROM generate_series(1, 5000);"
```
**macOS / Linux**
```bash
docker compose exec db psql -U postgres -d eventsdb -c \
"INSERT INTO events (occurred_at, lat, lon, type, severity)
 SELECT NOW() - (random() * interval '30 days'),
        41.0 + random()*1.5,
       -96.6 + random()*2.0,
        'demo',
        (floor(random()*5))::int
 FROM generate_series(1, 5000);"
```

**Sanity Check (Check for cluster events)**
```bash
docker compose exec db psql -U postgres -d eventsdb -c "SELECT count(*) FROM events;"
# expect ~5000
```

4) **Open the UI**
- Visit **http://localhost:5173**
- Pan/Zoom or move the H3 Res Slider to refresh the hex bins

> You don’t need to run `npm run dev` locally when using Docker. The frontend container serves the app.

> Don’t run the Docker frontend and local npm run dev at the same time.


### Alternative: Local UI dev (optional)
Run only if you want hot-reload outside Docker (backend can stay in Docker).

```bash
cd frontend
npm ci
npm run dev
# open the printed localhost URL (usually http://localhost:5173)
```
### Rebuilding Docker After Changes:
**Quick Rebuild (Keeps Data)**
```bash
docker compose up -d --build
```

### Clean Restart (recreate containers & Volumes):
**Quick Rebuild (Keeps Data)**
```bash
docker compose down -v
docker compose up --build
```

---

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






