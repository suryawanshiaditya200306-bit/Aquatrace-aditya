"""Geo-temporal spill–vessel correlation using AIS tracks.

Falls back is handled by callers (mock_sih) when AIS CSV is unavailable.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Optional

from backend.schemas.correlation import VesselCorrelationCandidate
from backend.schemas.spill import SpillFootprint
from backend.services import ais_service, mock_sih

# Prototype thresholds
SPATIAL_MATCH_KM = 25.0
SPATIAL_ZERO_KM = 250.0
TEMPORAL_MATCH_SCORE = 0.45
SPATIAL_MATCH_SCORE = 0.45

# Reference spill observation time for temporal windowing (prototype)
SPILL_OBSERVED_AT = datetime(2026, 9, 7, 14, 0, 0, tzinfo=timezone.utc)


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def _parse_ts(value: str) -> Optional[datetime]:
    raw = (value or "").strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


def _spatial_score(distance_km: float) -> float:
    if distance_km <= SPATIAL_MATCH_KM:
        # Inside near field: 1.0 at 0 km → ~0.7 at match radius
        return max(0.7, 1.0 - (distance_km / SPATIAL_MATCH_KM) * 0.3)
    if distance_km >= SPATIAL_ZERO_KM:
        return 0.0
    # Linear decay from 0.7 at match radius to 0 at zero radius
    t = (distance_km - SPATIAL_MATCH_KM) / (SPATIAL_ZERO_KM - SPATIAL_MATCH_KM)
    return max(0.0, 0.7 * (1.0 - t))


def _min_distance_to_spill_km(
    points: list[tuple[float, float]],
    footprint: SpillFootprint,
) -> float:
    refs = [(footprint.centroid.lat, footprint.centroid.lon)]
    refs.extend((p.lat, p.lon) for p in footprint.polygon)
    best = float("inf")
    for lat, lon in points:
        for rlat, rlon in refs:
            best = min(best, _haversine_km(lat, lon, rlat, rlon))
    return best if best < float("inf") else SPATIAL_ZERO_KM


def _temporal_score(
    timestamps: list[str],
    *,
    window_hours: float,
    spill_time: datetime = SPILL_OBSERVED_AT,
) -> tuple[float, str]:
    if not timestamps:
        return 0.0, "No AIS timestamps on track"

    parsed = [t for t in (_parse_ts(x) for x in timestamps) if t is not None]
    if not parsed:
        return 0.0, "Could not parse AIS timestamps"

    window_sec = window_hours * 3600.0
    deltas = [abs((t - spill_time).total_seconds()) for t in parsed]
    in_window = sum(1 for d in deltas if d <= window_sec)
    min_delta_h = min(deltas) / 3600.0

    if in_window == 0:
        # Soft decay outside window up to 2x window
        if min_delta_h >= window_hours * 2:
            return 0.0, f"Nearest AIS fix {min_delta_h:.1f}h from spill time (outside window)"
        score = max(0.0, 0.4 * (1.0 - (min_delta_h - window_hours) / window_hours))
        return score, f"Nearest AIS fix {min_delta_h:.1f}h from spill; 0 points in window"

    # Fraction of points in window, boosted if closest is very near spill time
    frac = in_window / len(parsed)
    closeness = max(0.0, 1.0 - (min_delta_h / max(window_hours, 1e-6)))
    score = min(1.0, 0.55 * frac + 0.45 * closeness)
    return score, f"{in_window}/{len(parsed)} AIS fixes within {window_hours:.0f}h window"


def correlate_vessel(
    vessel_id: str,
    *,
    footprint: SpillFootprint,
    time_window_hours: float,
) -> Optional[VesselCorrelationCandidate]:
    detail = ais_service.get_vessel_detail(vessel_id)
    traj = ais_service.get_trajectory(vessel_id)
    if detail is None or traj is None:
        return None

    points = [(p.lat, p.lon) for p in traj["points"]]
    timestamps = [p.timestamp for p in traj["points"]]
    if not points:
        points = [(detail.lat, detail.lon)]
        timestamps = [detail.last_ais_timestamp]

    distance_km = round(_min_distance_to_spill_km(points, footprint), 2)
    spatial = round(_spatial_score(distance_km), 3)
    temporal, temporal_note = _temporal_score(timestamps, window_hours=time_window_hours)
    temporal = round(temporal, 3)

    matched = spatial >= SPATIAL_MATCH_SCORE and temporal >= TEMPORAL_MATCH_SCORE
    notes = (
        f"min_dist={distance_km}km; spatial={spatial:.2f}; {temporal_note}"
    )

    return VesselCorrelationCandidate(
        vessel_id=vessel_id,
        vessel_name=detail.name,
        mmsi=detail.mmsi,
        spatial_overlap_score=spatial,
        temporal_overlap_score=temporal,
        distance_to_spill_km=distance_km,
        matched=matched,
        notes=notes,
    )


def correlate_vessels(
    vessel_ids: Optional[list[str]] = None,
    *,
    time_window_hours: float = 12.0,
    footprint: Optional[SpillFootprint] = None,
) -> list[VesselCorrelationCandidate]:
    """Correlate AIS vessels against the spill footprint."""
    fp = footprint or mock_sih.SPILL_FOOTPRINT
    ids = vessel_ids or ais_service.list_vessel_ids()
    out: list[VesselCorrelationCandidate] = []
    for vid in ids:
        candidate = correlate_vessel(vid, footprint=fp, time_window_hours=time_window_hours)
        if candidate is not None:
            out.append(candidate)
    out.sort(
        key=lambda c: (c.spatial_overlap_score + c.temporal_overlap_score) / 2.0,
        reverse=True,
    )
    return out
