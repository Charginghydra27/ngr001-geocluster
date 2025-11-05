"""
Script to load external weather databases into the system.
This supplements the existing manual data without replacing it.
"""
import sys
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .data_loaders import load_noaa_severe_weather, load_us_weather_events
from .models import Base
from .crud import bulk_insert_events

DATABASE_URL = os.getenv("DATABASE_URL")

def load_databases(noaa_path: str, us_weather_path: str, limit_per_db: int = None):
    """
    Load both external databases into the system.
    
    Args:
        noaa_path: Path to NOAA severe weather CSV file
        us_weather_path: Path to US weather events CSV file
        limit_per_db: Optional limit on records to load per database (for testing)
    """
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    print("Loading NOAA Severe Weather data...")
    noaa_count = 0
    db = SessionLocal()
    try:
        for batch in load_noaa_severe_weather(noaa_path, batch_size=5000):
            if limit_per_db and noaa_count >= limit_per_db:
                break
            inserted = bulk_insert_events(db, batch)
            noaa_count += inserted
            print(f"  Loaded {noaa_count} NOAA records...")
            if limit_per_db and noaa_count >= limit_per_db:
                break
    finally:
        db.close()
    
    print(f"\nCompleted NOAA load: {noaa_count} records")
    
    print("\nLoading US Weather Events data...")
    us_weather_count = 0
    db = SessionLocal()
    try:
        for batch in load_us_weather_events(us_weather_path, batch_size=5000):
            if limit_per_db and us_weather_count >= limit_per_db:
                break
            inserted = bulk_insert_events(db, batch)
            us_weather_count += inserted
            print(f"  Loaded {us_weather_count} US Weather records...")
            if limit_per_db and us_weather_count >= limit_per_db:
                break
    finally:
        db.close()
    
    print(f"\nCompleted US Weather load: {us_weather_count} records")
    print(f"\nTotal external records loaded: {noaa_count + us_weather_count}")
    print("These records supplement the existing manual data in the system.")

if __name__ == "__main__":
    noaa_csv = Path("/data/noaa-severe-weather/hail-2015.csv")
    us_weather_csv = Path("/data/us-weather-events/WeatherEvents_Jan2016-Dec2022.csv")
    
    limit = None
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
            print(f"Loading with limit of {limit} records per database")
        except ValueError:
            print("Invalid limit argument, loading all records")
    
    load_databases(str(noaa_csv), str(us_weather_csv), limit_per_db=limit)
