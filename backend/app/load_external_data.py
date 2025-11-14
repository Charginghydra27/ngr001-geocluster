""" 
Load external datasets into the database. 
This supplements the existing manual seeding without replacing it.
"""

import sys
from pathlib import Path
from .data_loaders import load_noaa_severe_weather, load_us_weather_events
from .crud import bulk_insert_events
from .db import SessionLocal

def load_databases(noaa_path: str, us_weather_path: str, limit_per_db: int | None = None):
    print("\n--- Loading NOAA Severe Weather ---")
    total_noaa = 0
    with SessionLocal() as db:
        for batch in load_noaa_severe_weather(noaa_path, batch_size=5000):
            if limit_per_db and total_noaa >= limit_per_db:
                break
            total_noaa += bulk_insert_events(db, batch)
    print(f" Loaded NOAA records: {total_noaa}")

    print("\n--- Loading US Weather Events ---")
    total_us = 0
    with SessionLocal() as db:
        for batch in load_us_weather_events(us_weather_path, batch_size=5000):
            if limit_per_db and total_us >= limit_per_db:
                break
            total_us += bulk_insert_events(db, batch)
    print(f" Loaded US Weather records: {total_us}")

    print("\nDone.")
    print(f"Total imported: {total_noaa + total_us}")


if __name__ == "__main__":
    noaa_csv = Path("/data/hail-2015.csv") 
    us_weather_csv = Path("/data/WeatherEvents_Jan2016-Dec2022.csv")

    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    load_databases(str(noaa_csv), str(us_weather_csv), limit_per_db=limit)
