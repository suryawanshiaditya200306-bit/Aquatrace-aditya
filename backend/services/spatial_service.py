import csv
import logging
import math
from typing import List, Dict, Any
from sqlalchemy import text
from backend.db.session import SessionLocal, is_db_reachable, DB_CONNECTION_ERRORS

logger = logging.getLogger("aquaslick.spatial")

def get_vessels_near_point(lat: float, lon: float, radius_km: float = 50.0) -> List[Dict[str, Any]]:
    """
    Primary: Native PostGIS spatial radius query.
    Fallback: Local CSV calculation if DB is unreachable.
    """
    if is_db_reachable():
        try:
            db = SessionLocal()
            query = text("""
                SELECT 
                    v.vessel_id, v.name, v.mmsi, v.vessel_type,
                    t.latitude, t.longitude, t.sog,
                    ST_Distance(
                        t.location::geography,
                        ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography
                    ) / 1000.0 AS distance_km
                FROM ais_tracks t
                JOIN vessels v ON v.vessel_id = t.vessel_id
                WHERE ST_DWithin(
                    t.location::geography,
                    ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                    :radius_m
                )
                ORDER BY distance_km ASC;
            """)
            result = db.execute(query, {
                "lat": lat,
                "lon": lon,
                "radius_m": radius_km * 1000.0
            }).mappings().all()
            db.close()
            return [dict(r) for r in result]
        except DB_CONNECTION_ERRORS as exc:
            logger.warning("DB unavailable during spatial query; switching to CSV fallback: %s", exc)

    # Local CSV Fallback
    logger.info("Executing local CSV spatial search fallback.")
    fallback_vessels = []
    try:
        with open("data/ais/sample_ais.csv", mode="r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                r_lat = float(row["latitude"])
                r_lon = float(row["longitude"])
                approx_dist = math.hypot((r_lat - lat) * 111.0, (r_lon - lon) * 111.0)
                if approx_dist <= radius_km:
                    fallback_vessels.append({
                        "vessel_id": row["mmsi"],
                        "name": row.get("name", "Unknown"),
                        "mmsi": row["mmsi"],
                        "vessel_type": row.get("vessel_type", "Unknown"),
                        "latitude": r_lat,
                        "longitude": r_lon,
                        "sog": float(row.get("sog", 0.0)),
                        "distance_km": round(approx_dist, 2),
                    })
    except Exception as err:
        logger.error("CSV fallback failed: %s", err)
    return fallback_vessels