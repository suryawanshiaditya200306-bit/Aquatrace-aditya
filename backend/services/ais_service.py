"""Local AIS CSV processing — no database.

Loads AIS records from disk, derives vessel lists / tracks / basic anomalies.
Falls back to mock_sih when no CSV is available.
"""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from backend.schemas.trajectory import TrajectoryPoint
from backend.schemas.vessels import VesselDetailResponse, VesselSummary

# Default search location for prototype AIS files
AIS_DIR = Path(__file__).resolve().parents[2] / "data" / "ais"
DEFAULT_CSV_CANDIDATES = (
    Path(os.getenv("AQUASLICK_AIS_CSV", "")) if os.getenv("AQUASLICK_AIS_CSV") else None,
    AIS_DIR / "sample_ais.csv",
)

# Anomaly thresholds (prototype defaults)
SPEED_CHANGE_KTS = float(os.getenv("AQUASLICK_AIS_SPEED_DELTA", "4.0"))
COURSE_CHANGE_DEG = float(os.getenv("AQUASLICK_AIS_COURSE_DELTA", "40.0"))

COLUMN_ALIASES = {
    "mmsi": ("mmsi", "mmsi_id", "userid"),
    "timestamp": ("timestamp", "time", "datetime", "base_date_time", "basedatetime"),
    "latitude": ("latitude", "lat", "ilat"),
    "longitude": ("longitude", "lon", "lng", "long", "ilon"),
    "sog": ("sog", "speed", "speed_kts", "speedoverground"),
    "cog": ("cog", "course", "course_deg", "courseoverground"),
    "heading": ("heading", "heading_deg", "true_heading", "head"),
    "vessel_type": ("vessel_type", "shiptype", "ship_type", "type", "vesseltype"),
    "name": ("name", "vessel_name", "shipname", "vessel"),
}


@dataclass
class AisRecord:
    mmsi: str
    timestamp: str
    lat: float
    lon: float
    sog: Optional[float] = None
    cog: Optional[float] = None
    heading: Optional[float] = None
    vessel_type: str = "Unknown"
    name: Optional[str] = None


@dataclass
class AisStore:
    source: str = "mock"  # csv | mock
    csv_path: Optional[str] = None
    records_by_mmsi: dict[str, list[AisRecord]] = field(default_factory=dict)
    # Stable frontend-friendly ids: mmsi -> vessel_id (v1.. or mmsi)
    id_by_mmsi: dict[str, str] = field(default_factory=dict)
    mmsi_by_id: dict[str, str] = field(default_factory=dict)


_STORE = AisStore()
_LOADED = False

# Preserve AquaTrace id mapping when MMSIs match the demo set
_KNOWN_MMSI_TO_ID = {
    "419000123": "v1",
    "419000888": "v2",
    "000000001": "v3",
    "UNKNOWN": "v3",
    "419000456": "v4",
}


def _normalize_header(name: str) -> str:
    return "".join(ch for ch in name.strip().lower() if ch.isalnum() or ch == "_")


def _map_row(headers: list[str]) -> dict[str, int]:
    normalized = {_normalize_header(h): i for i, h in enumerate(headers)}
    mapping: dict[str, int] = {}
    for field_name, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            key = _normalize_header(alias)
            if key in normalized:
                mapping[field_name] = normalized[key]
                break
    return mapping


def _parse_float(value: str) -> Optional[float]:
    value = (value or "").strip()
    if value == "" or value.upper() in {"NA", "NAN", "NULL", "NONE"}:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _parse_timestamp(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    # Keep ISO-ish strings as-is; otherwise return raw
    return raw.replace(" ", "T") if "T" not in raw and " " in raw else raw


def _angle_delta(a: float, b: float) -> float:
    """Smallest absolute difference between two compass angles (0-360)."""
    d = abs(a - b) % 360.0
    return d if d <= 180.0 else 360.0 - d


def _resolve_csv_path() -> Optional[Path]:
    for candidate in DEFAULT_CSV_CANDIDATES:
        if candidate is None:
            continue
        path = Path(candidate)
        if path.is_file() and path.stat().st_size > 0:
            return path
    # Any other csv in data/ais/
    if AIS_DIR.is_dir():
        for path in sorted(AIS_DIR.glob("*.csv")):
            if path.stat().st_size > 0:
                return path
    return None


def _assign_ids(mmsis: list[str]) -> tuple[dict[str, str], dict[str, str]]:
    id_by_mmsi: dict[str, str] = {}
    mmsi_by_id: dict[str, str] = {}
    auto_idx = 1
    for mmsi in mmsis:
        if mmsi in _KNOWN_MMSI_TO_ID:
            vid = _KNOWN_MMSI_TO_ID[mmsi]
        else:
            vid = f"ais_{mmsi}"
            # Avoid collisions
            while vid in mmsi_by_id:
                vid = f"ais_{mmsi}_{auto_idx}"
                auto_idx += 1
        id_by_mmsi[mmsi] = vid
        mmsi_by_id[vid] = mmsi
    return id_by_mmsi, mmsi_by_id


def load_ais_csv(path: Optional[Path] = None) -> AisStore:
    """Load AIS CSV into memory. Returns store with source=mock if unavailable."""
    global _STORE, _LOADED
    csv_path = path or _resolve_csv_path()
    if csv_path is None:
        _STORE = AisStore(source="mock", csv_path=None)
        _LOADED = True
        return _STORE

    records_by_mmsi: dict[str, list[AisRecord]] = {}
    with csv_path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.reader(fh)
        try:
            headers = next(reader)
        except StopIteration:
            _STORE = AisStore(source="mock", csv_path=str(csv_path))
            _LOADED = True
            return _STORE

        col = _map_row(headers)
        required = ("mmsi", "timestamp", "latitude", "longitude")
        if any(k not in col for k in required):
            _STORE = AisStore(source="mock", csv_path=str(csv_path))
            _LOADED = True
            return _STORE

        for row in reader:
            if not row or all(not c.strip() for c in row):
                continue
            try:
                mmsi = str(row[col["mmsi"]]).strip()
                lat = _parse_float(row[col["latitude"]])
                lon = _parse_float(row[col["longitude"]])
                if not mmsi or lat is None or lon is None:
                    continue
                sog = _parse_float(row[col["sog"]]) if "sog" in col else None
                cog = _parse_float(row[col["cog"]]) if "cog" in col else None
                heading = _parse_float(row[col["heading"]]) if "heading" in col else None
                vtype = (
                    row[col["vessel_type"]].strip()
                    if "vessel_type" in col and row[col["vessel_type"]].strip()
                    else "Unknown"
                )
                name = (
                    row[col["name"]].strip()
                    if "name" in col and row[col["name"]].strip()
                    else None
                )
                rec = AisRecord(
                    mmsi=mmsi,
                    timestamp=_parse_timestamp(row[col["timestamp"]]),
                    lat=lat,
                    lon=lon,
                    sog=sog,
                    cog=cog,
                    heading=heading,
                    vessel_type=vtype,
                    name=name,
                )
                records_by_mmsi.setdefault(mmsi, []).append(rec)
            except (IndexError, ValueError):
                continue

    for mmsi, recs in records_by_mmsi.items():
        recs.sort(key=lambda r: r.timestamp)

    id_by_mmsi, mmsi_by_id = _assign_ids(sorted(records_by_mmsi.keys()))
    _STORE = AisStore(
        source="csv" if records_by_mmsi else "mock",
        csv_path=str(csv_path),
        records_by_mmsi=records_by_mmsi,
        id_by_mmsi=id_by_mmsi,
        mmsi_by_id=mmsi_by_id,
    )
    _LOADED = True
    return _STORE


def ensure_loaded() -> AisStore:
    global _LOADED
    if not _LOADED:
        load_ais_csv()
    return _STORE


def reload_ais() -> AisStore:
    return load_ais_csv()


def using_csv() -> bool:
    return ensure_loaded().source == "csv"


def status() -> dict[str, Any]:
    store = ensure_loaded()
    n_records = sum(len(v) for v in store.records_by_mmsi.values())
    return {
        "status": "ok",
        "source": store.source,
        "csv_path": store.csv_path,
        "vessel_count": len(store.records_by_mmsi),
        "record_count": n_records,
        "message": (
            f"AIS loaded from CSV ({n_records} records)."
            if store.source == "csv"
            else "No AIS CSV found — using mock vessel data."
        ),
    }


def list_vessel_ids() -> list[str]:
    store = ensure_loaded()
    if store.source != "csv":
        return []
    return list(store.mmsi_by_id.keys())


def _latest(recs: list[AisRecord]) -> AisRecord:
    return recs[-1]


def list_vessel_summaries() -> list[VesselSummary]:
    store = ensure_loaded()
    if store.source != "csv":
        return []
    out: list[VesselSummary] = []
    for mmsi, recs in store.records_by_mmsi.items():
        last = _latest(recs)
        vid = store.id_by_mmsi[mmsi]
        out.append(
            VesselSummary(
                vessel_id=vid,
                name=last.name or f"MMSI {mmsi}",
                mmsi=mmsi if mmsi != "000000001" else "UNKNOWN",
                vessel_type=last.vessel_type,
                speed_kts=float(last.sog or 0.0),
                heading_deg=float(last.heading if last.heading is not None else (last.cog or 0.0)),
                lat=last.lat,
                lon=last.lon,
                last_ais_timestamp=last.timestamp,
                flag=None,
            )
        )
    out.sort(key=lambda v: v.vessel_id)
    return out


def get_vessel_detail(vessel_id: str) -> Optional[VesselDetailResponse]:
    store = ensure_loaded()
    if store.source != "csv":
        return None
    mmsi = store.mmsi_by_id.get(vessel_id)
    if not mmsi:
        return None
    recs = store.records_by_mmsi.get(mmsi)
    if not recs:
        return None
    last = _latest(recs)
    display_mmsi = "UNKNOWN" if mmsi == "000000001" else mmsi
    return VesselDetailResponse(
        vessel_id=vessel_id,
        name=last.name or f"MMSI {display_mmsi}",
        mmsi=display_mmsi,
        vessel_type=last.vessel_type,
        speed_kts=float(last.sog or 0.0),
        heading_deg=float(last.heading if last.heading is not None else (last.cog or 0.0)),
        lat=last.lat,
        lon=last.lon,
        last_ais_timestamp=last.timestamp,
        flag=None,
        destination=None,
        draught_m=None,
        length_m=None,
        ais_status="under_way",
        message="Vessel detail derived from local AIS CSV.",
    )


def get_trajectory(vessel_id: str) -> Optional[dict[str, Any]]:
    store = ensure_loaded()
    if store.source != "csv":
        return None
    mmsi = store.mmsi_by_id.get(vessel_id)
    if not mmsi:
        return None
    recs = store.records_by_mmsi.get(mmsi)
    if not recs:
        return None
    last = _latest(recs)
    points = [
        TrajectoryPoint(
            lat=r.lat,
            lon=r.lon,
            timestamp=r.timestamp,
            speed_kts=r.sog,
            heading_deg=r.heading if r.heading is not None else r.cog,
            course_deg=r.cog,
        )
        for r in recs
    ]
    track_hours = 0.0
    if len(recs) >= 2:
        # Rough span from first/last timestamp strings when ISO-like
        track_hours = max(1.0, float(len(recs) - 1) * 2.0)
    display_mmsi = "UNKNOWN" if mmsi == "000000001" else mmsi
    return {
        "vessel_id": vessel_id,
        "vessel_name": last.name or f"MMSI {display_mmsi}",
        "mmsi": display_mmsi,
        "points": points,
        "track_hours": track_hours,
        "message": "Trajectory derived from local AIS CSV.",
    }


def detect_anomalies(
    vessel_id: str,
    *,
    speed_delta_kts: float = SPEED_CHANGE_KTS,
    course_delta_deg: float = COURSE_CHANGE_DEG,
) -> Optional[dict[str, Any]]:
    store = ensure_loaded()
    if store.source != "csv":
        return None
    mmsi = store.mmsi_by_id.get(vessel_id)
    if not mmsi:
        return None
    recs = store.records_by_mmsi.get(mmsi, [])
    anomalies: list[dict[str, Any]] = []

    for prev, curr in zip(recs, recs[1:]):
        if prev.sog is not None and curr.sog is not None:
            ds = abs(curr.sog - prev.sog)
            if ds >= speed_delta_kts:
                anomalies.append(
                    {
                        "type": "sudden_speed_change",
                        "timestamp": curr.timestamp,
                        "lat": curr.lat,
                        "lon": curr.lon,
                        "magnitude": round(ds, 2),
                        "unit": "kts",
                        "detail": f"SOG changed by {ds:.1f} kts ({prev.sog:.1f} -> {curr.sog:.1f})",
                    }
                )

        prev_course = prev.cog if prev.cog is not None else prev.heading
        curr_course = curr.cog if curr.cog is not None else curr.heading
        if prev_course is not None and curr_course is not None:
            dc = _angle_delta(prev_course, curr_course)
            if dc >= course_delta_deg:
                anomalies.append(
                    {
                        "type": "sharp_course_change",
                        "timestamp": curr.timestamp,
                        "lat": curr.lat,
                        "lon": curr.lon,
                        "magnitude": round(dc, 2),
                        "unit": "deg",
                        "detail": f"Course changed by {dc:.1f} deg ({prev_course:.1f} -> {curr_course:.1f})",
                    }
                )

    display_mmsi = "UNKNOWN" if mmsi == "000000001" else mmsi
    last = _latest(recs) if recs else None
    return {
        "status": "ok",
        "vessel_id": vessel_id,
        "vessel_name": (last.name if last and last.name else f"MMSI {display_mmsi}"),
        "mmsi": display_mmsi,
        "anomaly_count": len(anomalies),
        "anomalies": anomalies,
        "thresholds": {
            "speed_change_kts": speed_delta_kts,
            "course_change_deg": course_delta_deg,
        },
        "message": (
            f"Detected {len(anomalies)} anomal{'y' if len(anomalies) == 1 else 'ies'} "
            "from AIS track."
            if anomalies
            else "No speed/course anomalies above thresholds."
        ),
    }
