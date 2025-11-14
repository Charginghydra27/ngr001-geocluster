import csv
from datetime import datetime
from typing import Iterator
from pathlib import Path
from .schemas import EventIn

def parse_noaa_hail_timestamp(ztime_str: str) -> datetime:
    """Parse NOAA ZTIME format: YYYYMMDDHHMMSS"""
    year = int(ztime_str[0:4])
    month = int(ztime_str[4:6])
    day = int(ztime_str[6:8])
    hour = int(ztime_str[8:10])
    minute = int(ztime_str[10:12])
    second = int(ztime_str[12:14])
    return datetime(year, month, day, hour, minute, second)


def load_noaa_severe_weather(csv_path: str, batch_size: int = 1000) -> Iterator[list[EventIn]]:
    """
    Load NOAA severe weather data (hail events) from CSV.
    Yields batches of EventIn objects.
    
    CSV columns: X.ZTIME, LON, LAT, WSR_ID, CELL_ID, RANGE, AZIMUTH, SEVPROB, PROB, MAXSIZE
    """
    path = Path(csv_path)
    if not path.exists():
        print(f"[ERROR] File not found: {csv_path}")
        return
    
    batch = []
    row_count = 0
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            row_count += 1
            try:
                occurred_at = parse_noaa_hail_timestamp(row['X.ZTIME'])
                lat = float(row['LAT'])
                lon = float(row['LON'])
                
                severity_prob = int(row.get('SEVPROB', 0))
                max_size = float(row.get('MAXSIZE', 0))
                
                # Severity classification
                severity = 1
                if severity_prob >= 80 or max_size >= 2.0:
                    severity = 5
                elif severity_prob >= 60 or max_size >= 1.5:
                    severity = 4
                elif severity_prob >= 40 or max_size >= 1.0:
                    severity = 3
                elif severity_prob >= 20 or max_size >= 0.75:
                    severity = 2
                
                event = EventIn(
                    occurred_at=occurred_at,
                    lat=lat,
                    lon=lon,
                    type="hail",
                    severity=severity,
                    properties={
                        "source": "noaa_severe_weather",
                        "wsr_id": row.get('WSR_ID', ''),
                        "cell_id": row.get('CELL_ID', ''),
                        "severity_prob": severity_prob,
                        "max_size_inches": max_size,
                        "range": float(row.get('RANGE', 0)),
                        "azimuth": int(row.get('AZIMUTH', 0))
                    }
                )
                batch.append(event)
                
                if len(batch) >= batch_size:
                    yield batch
                    batch = []
                    
            except (ValueError, KeyError) as e:
                print(f"[WARN] Skipped row #{row_count} due to parse error: {e}")
                continue
    
    if batch:
        yield batch


def load_us_weather_events(csv_path: str, batch_size: int = 1000) -> Iterator[list[EventIn]]:
    """
    Load US Weather Events from CSV and yield batches of EventIn objects.
    """
    path = Path(csv_path)
    if not path.exists():
        print(f"[ERROR] File not found: {csv_path}")
        return

    severity_map = {
        'light': 1,
        'moderate': 3,
        'heavy': 4,
        'severe': 5,
        'unk': 2
    }

    batch = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=1):
            try:
                occurred_at = datetime.strptime(row['StartTime(UTC)'], '%Y-%m-%d %H:%M:%S')
                lat = float(row['LocationLat'])
                lon = float(row['LocationLng'])
                event_type = row['Type'].lower()
                severity = severity_map.get(row['Severity'].lower().strip(), 2)

                end_time = None
                if row.get('EndTime(UTC)'):
                    try:
                        end_time = datetime.strptime(row['EndTime(UTC)'], '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        pass

                precipitation = float(row.get('Precipitation(in)', 0) or 0)

                batch.append(EventIn(
                    occurred_at=occurred_at,
                    lat=lat,
                    lon=lon,
                    type=event_type,
                    severity=severity,
                    properties={
                        "source": "us_weather_events",
                        "event_id": row.get('EventId', ''),
                        "end_time": end_time.isoformat() if end_time else None,
                        "precipitation_inches": precipitation,
                        "airport_code": row.get('AirportCode', ''),
                        "city": row.get('City', ''),
                        "county": row.get('County', ''),
                        "state": row.get('State', ''),
                        "zipcode": row.get('ZipCode', '')
                    }
                ))

                if len(batch) >= batch_size:
                    yield batch
                    batch = []

            except Exception as e:
                print(f"[WARN] Skipping row {i}: {e}")

    if batch:
        yield batch
