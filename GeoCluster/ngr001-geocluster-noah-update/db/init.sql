CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS events (
  id SERIAL PRIMARY KEY,
  occurred_at TIMESTAMPTZ NOT NULL,
  lat DOUBLE PRECISION NOT NULL,
  lon DOUBLE PRECISION NOT NULL,
  type TEXT,
  severity INTEGER,
  properties JSONB DEFAULT '{}'::jsonb
);

ALTER TABLE events
  ADD COLUMN IF NOT EXISTS geom GEOGRAPHY(Point,4326)
  GENERATED ALWAYS AS (ST_SetSRID(ST_MakePoint(lon, lat), 4326)::geography) STORED;

CREATE INDEX IF NOT EXISTS idx_events_geom ON events USING gist ((geom::geometry));
CREATE INDEX IF NOT EXISTS idx_events_time ON events USING brin (occurred_at);
CREATE INDEX IF NOT EXISTS idx_events_type ON events (type);
