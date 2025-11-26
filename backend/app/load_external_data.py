"""
Load external datasets into the database.
This supplements the existing manual seeding without replacing it.

Sources supported:
 - NOAA Severe Weather (hail)            -> hail-2015.csv
 - US Weather Events (2016–2022)         -> WeatherEvents_Jan2016-Dec2022.csv
 - US Accidents (sobhanmoosavi dataset)  -> US_Accidents_March23.csv
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable, Iterable, Optional, List

from .data_loaders import (
    load_noaa_severe_weather,
    load_us_weather_events,
    load_us_accidents,
)
from .crud import bulk_insert_events
from .db import SessionLocal
from .schemas import EventIn


def _ingest(
    label: str,
    csv_path: Path,
    loader_fn: Callable[[str, int], Iterable[List[EventIn]]],
    limit: Optional[int],
    batch_size: int = 5_000,
) -> int:
    """Ingest one dataset using the provided loader; returns rows inserted."""
    print(f"\n--- Loading {label} ---")

    if not csv_path.exists():
        print(f" [SKIP] File not found: {csv_path}")
        return 0

    total = 0
    with SessionLocal() as db:
        for batch in loader_fn(str(csv_path), batch_size=batch_size):
            if limit is not None and total >= limit:
                break
            total += bulk_insert_events(db, batch)

    print(f" Loaded {label} records: {total}")
    return total


def load_databases(
    noaa_path: str | Path,
    us_weather_path: str | Path,
    us_accidents_path: str | Path,
    limit_per_source: Optional[int] = None,
) -> None:
    """
    Load all supported external datasets.
      - limit_per_source: max rows to import **per dataset** (None = no cap)
    """
    total_noaa = _ingest(
        "NOAA Severe Weather (hail)",
        Path(noaa_path),
        load_noaa_severe_weather,
        limit_per_source,
    )

    total_us_weather = _ingest(
        "US Weather Events",
        Path(us_weather_path),
        load_us_weather_events,
        limit_per_source,
    )

    total_accidents = _ingest(
        "US Accidents",
        Path(us_accidents_path),
        load_us_accidents,
        limit_per_source,
    )

    grand_total = total_noaa + total_us_weather + total_accidents
    print("\nDone.")
    print(
        f"Totals -> NOAA: {total_noaa}, US Weather: {total_us_weather}, "
        f"US Accidents: {total_accidents}, GRAND: {grand_total}"
    )


if __name__ == "__main__":
    # Default container-mounted locations
    noaa_csv = Path("/data/hail-2015.csv")
    us_weather_csv = Path("/data/WeatherEvents_Jan2016-Dec2022.csv")
    us_acc_csv = Path("/data/US_Accidents_March23.csv")

    # Optional CLI limit: e.g., `python -m app.load_external_data 100000`
    limit: Optional[int]
    if len(sys.argv) > 1 and sys.argv[1].strip():
        try:
            limit = int(sys.argv[1])
        except ValueError:
            print(f"[WARN] Invalid limit '{sys.argv[1]}'; running without a limit.")
            limit = None
    else:
        limit = None

    load_databases(noaa_csv, us_weather_csv, us_acc_csv, limit_per_source=limit)
