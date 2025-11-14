import csv
import io
import re
from datetime import datetime
from typing import Iterator, List, Dict, Optional
from pathlib import Path
from .schemas import EventIn

# =========================
# Helpers: encoding + CSV
# =========================

_ENCODINGS = ("utf-8-sig", "cp1252", "latin-1")

def _sniff_dialect(sample: str) -> csv.Dialect:
    """Detect delimiter/quote via csv.Sniffer; default to excel if unsure."""
    sniffer = csv.Sniffer()
    try:
        return sniffer.sniff(sample, delimiters=[",", "\t", ";", "|"])
    except Exception:
        return csv.get_dialect("excel")

def _open_reader(path: str) -> csv.DictReader:
    """
    Try multiple encodings. Sniff delimiter from the first chunk.
    Returns a DictReader positioned at the start.
    Raises the last UnicodeDecodeError if all fail.
    """
    last_err = None
    for enc in _ENCODINGS:
        try:
            f = open(path, "r", encoding=enc, newline="")
            try:
                sample = f.read(65536)
            except UnicodeDecodeError as e:
                f.close()
                last_err = e
                continue
            f.seek(0)
            dialect = _sniff_dialect(sample)
            reader = csv.DictReader(f, dialect=dialect)
            # Attach the underlying file object so callers can close it later
            reader._io = f  # type: ignore[attr-defined]
            return reader
        except UnicodeDecodeError as e:
            last_err = e
            continue
    if last_err:
        raise last_err
    raise RuntimeError("Failed to open CSV with any known encoding.")

def _close_reader(reader: csv.DictReader) -> None:
    f = getattr(reader, "_io", None)
    if f:
        f.close()

def _norm(s: str | None) -> str:
    """lowercase, trim, remove non-alphanumerics for robust header matching."""
    return re.sub(r"[^a-z0-9]", "", (s or "").strip().lower())

def _first_key(row_or_headers, candidates: list[str]) -> Optional[str]:
    """
    Find the first header in row_or_headers (dict or list of headers) that
    matches any candidate (using normalized comparison).
    Returns the ORIGINAL header string.
    """
    if isinstance(row_or_headers, dict):
        headers = list(row_or_headers.keys())
    else:
        headers = list(row_or_headers)

    norm_map = { _norm(h): h for h in headers }
    cand_norm = [_norm(c) for c in candidates]

    # exact normalized match
    for c in cand_norm:
        if c in norm_map:
            return norm_map[c]

    # looser "contains" match
    for nk, orig in norm_map.items():
        if any(c in nk for c in cand_norm):
            return orig
    return None

# =========================
# NOAA Hail (SWDI)
# =========================

def _parse_noaa_time_flexible(z: str) -> datetime:
    """
    Accept YYYYMMDDHHMM or YYYYMMDDHHMMSS. Strip non-digits and pad seconds.
    """
    s = re.sub(r"\D", "", (z or ""))
    if len(s) == 12:
        s += "00"
    if len(s) != 14:
        raise ValueError(f"unexpected ZTIME length ({len(s)}): {z!r}")
    return datetime(
        int(s[0:4]), int(s[4:6]), int(s[6:8]),
        int(s[8:10]), int(s[10:12]), int(s[12:14])
    )

def load_noaa_severe_weather(csv_path: str, batch_size: int = 1000) -> Iterator[List[EventIn]]:
    """
    Robust NOAA hail loader.
    Tries flexible encodings, delimiter sniffing, and header aliases.
    """
    path = Path(csv_path)
    if not path.exists():
        print(f"[ERROR] File not found: {csv_path}")
        return

    batch: List[EventIn] = []
    reader = _open_reader(csv_path)
    try:
        # Resolve header names once from fieldnames
        headers = reader.fieldnames or []
        time_key = _first_key(headers, ["X.ZTIME", "X_ZTIME", "ZTIME", "X ZTIME", "Time", "X:ZTIME", "XZTIME"])
        lat_key  = _first_key(headers, ["LAT", "Latitude", "Y"])
        lon_key  = _first_key(headers, ["LON", "Longitude", "X"])

        if not (time_key and lat_key and lon_key):
            print(f"[ERROR] NOAA: could not resolve essential columns from headers: {headers[:10]}…")
            return

        for i, row in enumerate(reader, start=1):
            try:
                occurred_at = _parse_noaa_time_flexible(row.get(time_key, ""))
                lat = float((row.get(lat_key) or "").strip())
                lon = float((row.get(lon_key) or "").strip())

                sevprob = int((row.get("SEVPROB") or 0) or 0)
                maxsize = float((row.get("MAXSIZE") or 0) or 0)

                severity = 1
                if sevprob >= 80 or maxsize >= 2.0:   severity = 5
                elif sevprob >= 60 or maxsize >= 1.5: severity = 4
                elif sevprob >= 40 or maxsize >= 1.0: severity = 3
                elif sevprob >= 20 or maxsize >= 0.75:severity = 2

                evt = EventIn(
                    occurred_at=occurred_at,
                    lat=lat,
                    lon=lon,
                    type="hail",
                    severity=severity,
                    properties={
                        "source": "noaa_severe_weather",
                        "wsr_id": row.get("WSR_ID", ""),
                        "cell_id": row.get("CELL_ID", ""),
                        "severity_prob": sevprob,
                        "max_size_inches": maxsize,
                        "range": float((row.get("RANGE") or 0) or 0),
                        "azimuth": int((row.get("AZIMUTH") or 0) or 0),
                    },
                )
                batch.append(evt)
                if len(batch) >= batch_size:
                    yield batch
                    batch = []

            except Exception as e:
                # keep going; noisy datasets are expected
                if i <= 25:
                    print(f"[WARN] NOAA row {i} skipped: {e}")
                elif i == 26:
                    print("[WARN] NOAA: suppressing further row errors…")
                continue

    finally:
        _close_reader(reader)

    if batch:
        yield batch

# =========================
# US Weather Events
# =========================

def load_us_weather_events(csv_path: str, batch_size: int = 1000) -> Iterator[List[EventIn]]:
    """
    Robust US Weather Events loader (sobhanmoosavi/us-weather-events).
    Handles encoding quirks and minor header variations.
    """
    path = Path(csv_path)
    if not path.exists():
        print(f"[ERROR] File not found: {csv_path}")
        return

    severity_map = {
        "light": 1,
        "moderate": 3,
        "heavy": 4,
        "severe": 5,
        "unk": 2,
        "": 2,
    }

    batch: List[EventIn] = []
    reader = _open_reader(csv_path)
    try:
        headers = reader.fieldnames or []
        start_key = _first_key(headers, ["StartTime(UTC)", "Start_Time(UTC)", "StartTimeUTC", "Start Time (UTC)", "Start_Time", "StartTime"])
        end_key   = _first_key(headers, ["EndTime(UTC)", "End_Time(UTC)", "EndTimeUTC", "End Time (UTC)", "End_Time", "EndTime"])
        lat_key   = _first_key(headers, ["LocationLat", "Lat", "Latitude"])
        lng_key   = _first_key(headers, ["LocationLng", "Lng", "Long", "Longitude"])
        type_key  = _first_key(headers, ["Type", "EventType"])
        sev_key   = _first_key(headers, ["Severity"])

        if not (start_key and lat_key and lng_key and type_key and sev_key):
            print(f"[ERROR] US Weather: missing essential columns from headers: {headers[:10]}…")
            return

        for i, row in enumerate(reader, start=1):
            try:
                occurred_at = datetime.strptime(row[start_key].strip(), "%Y-%m-%d %H:%M:%S")
            except Exception:
                # try ISO-ish fallback
                try:
                    occurred_at = datetime.fromisoformat(row[start_key].strip().replace("Z", "").replace("T", " "))
                except Exception as e:
                    if i <= 25:
                        print(f"[WARN] US Weather row {i} time parse: {e}")
                    continue

            try:
                lat = float((row.get(lat_key) or "").strip())
                lon = float((row.get(lng_key) or "").strip())
            except Exception:
                if i <= 25:
                    print(f"[WARN] US Weather row {i} missing/invalid coords")
                continue

            event_type = (row.get(type_key) or "").strip().lower()
            sev_word = (row.get(sev_key) or "unk").strip().lower()
            severity = severity_map.get(sev_word, 2)

            end_iso = None
            if end_key and row.get(end_key):
                try:
                    end_dt = datetime.strptime(row[end_key].strip(), "%Y-%m-%d %H:%M:%S")
                    end_iso = end_dt.isoformat()
                except Exception:
                    try:
                        end_dt = datetime.fromisoformat(row[end_key].strip().replace("Z", "").replace("T", " "))
                        end_iso = end_dt.isoformat()
                    except Exception:
                        end_iso = None

            precip = 0.0
            for pkey in ("Precipitation(in)", "Precipitation", "PrecipIn"):
                if pkey in (reader.fieldnames or []):
                    try:
                        precip = float((row.get(pkey) or 0) or 0)
                    except Exception:
                        precip = 0.0
                    break

            evt = EventIn(
                occurred_at=occurred_at,
                lat=lat,
                lon=lon,
                type=event_type,
                severity=severity,
                properties={
                    "source": "us_weather_events",
                    "event_id": row.get("EventId", ""),
                    "end_time": end_iso,
                    "precipitation_inches": precip,
                    "airport_code": row.get("AirportCode", ""),
                    "city": row.get("City", ""),
                    "county": row.get("County", ""),
                    "state": row.get("State", ""),
                    "zipcode": row.get("ZipCode", ""),
                },
            )
            batch.append(evt)

            if len(batch) >= batch_size:
                yield batch
                batch = []

    finally:
        _close_reader(reader)

    if batch:
        yield batch

# =========================
# US Accidents
# =========================

def _parse_us_accidents_dt(s: str) -> Optional[datetime]:
    if not s:
        return None
    s2 = s.replace("T", " ").replace("Z", "")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s2, fmt)
        except Exception:
            pass
    try:
        return datetime.fromisoformat(s2)
    except Exception:
        return None

def load_us_accidents(csv_path: str, batch_size: int = 1000) -> Iterator[List[EventIn]]:
    """
    sobhanmoosavi/us-accidents (e.g., US_Accidents_March23.csv)
    """
    path = Path(csv_path)
    if not path.exists():
        print(f"[ERROR] File not found: {csv_path}")
        return

    batch: List[EventIn] = []
    reader = _open_reader(csv_path)
    try:
        headers = reader.fieldnames or []
        start_key = _first_key(headers, ["Start_Time", "StartTime", "Start Time"])
        lat_key   = _first_key(headers, ["Start_Lat", "Lat", "Latitude"])
        lng_key   = _first_key(headers, ["Start_Lng", "Lng", "Long", "Longitude"])
        sev_key   = _first_key(headers, ["Severity"])

        if not (start_key and lat_key and lng_key and sev_key):
            print(f"[ERROR] US Accidents: missing essential columns from headers: {headers[:10]}…")
            return

        for i, row in enumerate(reader, start=1):
            try:
                when = _parse_us_accidents_dt(row.get(start_key, ""))
                if when is None:
                    continue

                lat = float((row.get(lat_key) or "").strip())
                lon = float((row.get(lng_key) or "").strip())

                try:
                    sev_raw = int((row.get(sev_key) or 0) or 0)
                except Exception:
                    sev_raw = 0
                severity = max(1, min(sev_raw, 5))

                evt = EventIn(
                    occurred_at=when,
                    lat=lat,
                    lon=lon,
                    type="accident",
                    severity=severity,
                    properties={
                        "source": "us_accidents",
                        "city": row.get("City"),
                        "state": row.get("State"),
                        "id": row.get("ID"),
                    },
                )
                batch.append(evt)

                if len(batch) >= batch_size:
                    yield batch
                    batch = []

            except Exception as e:
                if i <= 25:
                    print(f"[WARN] US Accidents row {i} skipped: {e}")
                elif i == 26:
                    print("[WARN] US Accidents: suppressing further row errors…")
                continue

    finally:
        _close_reader(reader)

    if batch:
        yield batch
