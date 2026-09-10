import csv
import logging
from datetime import datetime, timezone
from pathlib import Path
from geoalchemy2.elements import WKTElement
from sqlalchemy.dialects.postgresql import insert
from backend.db.models import Vessel, AISTrack
from backend.db.session import SessionLocal, is_db_reachable

logger = logging.getLogger("aquaslick.ingest")

def ingest_sample_ais(csv_path: str = "data/ais/sample_ais.csv") -> int:
    """Idempotently ingests AIS CSV records into vessels and ais_tracks tables."""
    if not is_db_reachable():
        logger.warning("Database offline; skipping database ingestion.")
        return 0

    path = Path(csv_path)
    if not path.exists():
        logger.error("AIS CSV path not found: %s", csv_path)
        return 0

    db = SessionLocal()
    inserted_count = 0
    try:
        with open(path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                vessel_id = str(row["mmsi"])
                
                # Upsert vessel
                stmt_vessel = insert(Vessel).values(
                    vessel_id=vessel_id,
                    mmsi=str(row["mmsi"]),
                    name=row.get("name") or f"Vessel-{vessel_id}",
                    vessel_type=row.get("vessel_type"),
                    flag=row.get("flag"),
                ).on_conflict_do_update(
                    index_elements=["vessel_id"],
                    set_={"name": row.get("name") or f"Vessel-{vessel_id}"}
                )
                db.execute(stmt_vessel)

                # Parse coordinates and timestamp
                ts_str = row.get("timestamp")
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00")) if ts_str else datetime.now(timezone.utc)
                lat = float(row["latitude"])
                lon = float(row["longitude"])
                point_wkt = WKTElement(f"POINT({lon} {lat})", srid=4326)

                # Upsert AIS track point
                stmt_track = insert(AISTrack).values(
                    vessel_id=vessel_id,
                    timestamp=ts,
                    latitude=lat,
                    longitude=lon,
                    sog=float(row.get("sog", 0.0)),
                    cog=float(row.get("cog", 0.0)) if row.get("cog") else None,
                    heading=float(row.get("heading", 0.0)) if row.get("heading") else None,
                    location=point_wkt,
                ).on_conflict_do_nothing(
                    constraint="uq_vessel_track_time"
                )
                res = db.execute(stmt_track)
                if res.rowcount > 0:
                    inserted_count += 1

        db.commit()
        logger.info("AIS Ingestion finished. New points inserted: %d", inserted_count)
        return inserted_count
    except Exception as exc:
        db.rollback()
        logger.exception("Error during AIS CSV ingestion: %s", exc)
        raise
    finally:
        db.close()