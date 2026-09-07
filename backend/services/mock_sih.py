"""Shared mock SIH workflow data (East Coast corridor).

Mirrors the AquaTrace demo vessels so Streamlit can integrate later.
No database — in-memory placeholders only.
"""

from __future__ import annotations

from backend.schemas.correlation import VesselCorrelationCandidate
from backend.schemas.risk import RiskFactor, VesselRiskScore
from backend.schemas.spill import GeoPoint, SpillFootprint
from backend.schemas.trajectory import TrajectoryPoint
from backend.schemas.vessels import VesselDetailResponse, VesselSummary

DEFAULT_SPILL_ID = "spill_mock_east_coast_001"

SPILL_FOOTPRINT = SpillFootprint(
    polygon=[
        GeoPoint(lat=17.67, lon=83.63),
        GeoPoint(lat=17.71, lon=83.65),
        GeoPoint(lat=17.69, lon=83.69),
        GeoPoint(lat=17.65, lon=83.66),
    ],
    centroid=GeoPoint(lat=17.68, lon=83.66),
    area_sq_km=1.2,
)

_VESSELS: dict[str, dict] = {
    "v1": {
        "vessel_id": "v1",
        "name": "MT Sagar Ratna",
        "mmsi": "419000123",
        "vessel_type": "Crude Oil Tanker",
        "speed_kts": 11.4,
        "heading_deg": 48.0,
        "lat": 17.65,
        "lon": 83.66,
        "last_ais_timestamp": "2026-09-07T14:22:00Z",
        "flag": "IND",
        "destination": "Visakhapatnam",
        "draught_m": 12.4,
        "length_m": 248.0,
        "ais_status": "under_way",
        "path": [
            (17.35, 83.35, "2026-09-07T08:00:00Z", 10.8, 42.0),
            (17.46, 83.42, "2026-09-07T10:00:00Z", 11.0, 45.0),
            (17.58, 83.52, "2026-09-07T12:00:00Z", 11.2, 47.0),
            (17.69, 83.66, "2026-09-07T14:00:00Z", 11.4, 48.0),
            (17.78, 83.79, "2026-09-07T16:00:00Z", 11.1, 50.0),
        ],
        "spatial": 0.96,
        "temporal": 0.94,
        "distance_km": 0.4,
        "matched": True,
        "notes": "Track intersects spill polygon within the analysis window.",
        "risk": 0.96,
        "risk_level": "critical",
        "rationale": "Strong spatial-temporal overlap with spill centroid; tanker class elevates discharge risk.",
    },
    "v2": {
        "vessel_id": "v2",
        "name": "MV Crimson Tide",
        "mmsi": "419000888",
        "vessel_type": "Bulk Carrier",
        "speed_kts": 9.8,
        "heading_deg": 55.0,
        "lat": 16.98,
        "lon": 82.35,
        "last_ais_timestamp": "2026-09-07T13:50:00Z",
        "flag": "IND",
        "destination": "Kakinada",
        "draught_m": 10.1,
        "length_m": 189.0,
        "ais_status": "under_way",
        "path": [
            (16.70, 82.10, "2026-09-07T07:00:00Z", 9.2, 50.0),
            (16.85, 82.25, "2026-09-07T10:00:00Z", 9.5, 52.0),
            (16.98, 82.35, "2026-09-07T13:00:00Z", 9.8, 55.0),
            (17.15, 82.50, "2026-09-07T16:00:00Z", 9.6, 56.0),
        ],
        "spatial": 0.42,
        "temporal": 0.55,
        "distance_km": 145.0,
        "matched": False,
        "notes": "Outside spill AOI; temporal window only.",
        "risk": 0.28,
        "risk_level": "low",
        "rationale": "Far from spill footprint; low spatial overlap.",
    },
    "v3": {
        "vessel_id": "v3",
        "name": "Black Pearl (Rogue)",
        "mmsi": "UNKNOWN",
        "vessel_type": "Unregistered Tanker",
        "speed_kts": 14.1,
        "heading_deg": 62.0,
        "lat": 18.50,
        "lon": 84.80,
        "last_ais_timestamp": "2026-09-07T14:05:00Z",
        "flag": None,
        "destination": "Unknown",
        "draught_m": 11.8,
        "length_m": 220.0,
        "ais_status": "under_way",
        "path": [
            (18.10, 84.40, "2026-09-07T08:00:00Z", 13.5, 58.0),
            (18.30, 84.60, "2026-09-07T11:00:00Z", 13.9, 60.0),
            (18.50, 84.80, "2026-09-07T14:00:00Z", 14.1, 62.0),
            (18.75, 85.05, "2026-09-07T17:00:00Z", 14.0, 64.0),
        ],
        "spatial": 0.71,
        "temporal": 0.80,
        "distance_km": 98.0,
        "matched": True,
        "notes": "Partial proximity; missing MMSI increases uncertainty.",
        "risk": 0.78,
        "risk_level": "high",
        "rationale": "Unregistered AIS identity plus proximity to spill corridor.",
    },
    "v4": {
        "vessel_id": "v4",
        "name": "Oceanic Voyager",
        "mmsi": "419000456",
        "vessel_type": "Chemical Tanker",
        "speed_kts": 12.3,
        "heading_deg": 40.0,
        "lat": 20.15,
        "lon": 86.75,
        "last_ais_timestamp": "2026-09-07T12:40:00Z",
        "flag": "IND",
        "destination": "Paradip",
        "draught_m": 11.2,
        "length_m": 175.0,
        "ais_status": "under_way",
        "path": [
            (19.80, 86.40, "2026-09-07T06:00:00Z", 11.8, 38.0),
            (19.95, 86.60, "2026-09-07T09:00:00Z", 12.0, 39.0),
            (20.15, 86.75, "2026-09-07T12:00:00Z", 12.3, 40.0),
            (20.40, 86.95, "2026-09-07T15:00:00Z", 12.1, 42.0),
        ],
        "spatial": 0.35,
        "temporal": 0.40,
        "distance_km": 320.0,
        "matched": False,
        "notes": "Northern corridor; no footprint intersection.",
        "risk": 0.22,
        "risk_level": "low",
        "rationale": "Distant from spill; chemical tanker class alone is insufficient.",
    },
}


def list_vessel_summaries() -> list[VesselSummary]:
    return [
        VesselSummary(
            vessel_id=v["vessel_id"],
            name=v["name"],
            mmsi=v["mmsi"],
            vessel_type=v["vessel_type"],
            speed_kts=v["speed_kts"],
            heading_deg=v["heading_deg"],
            lat=v["lat"],
            lon=v["lon"],
            last_ais_timestamp=v["last_ais_timestamp"],
            flag=v["flag"],
        )
        for v in _VESSELS.values()
    ]


def get_vessel(vessel_id: str) -> dict | None:
    return _VESSELS.get(vessel_id)


def get_vessel_detail(vessel_id: str) -> VesselDetailResponse | None:
    v = _VESSELS.get(vessel_id)
    if not v:
        return None
    return VesselDetailResponse(
        vessel_id=v["vessel_id"],
        name=v["name"],
        mmsi=v["mmsi"],
        vessel_type=v["vessel_type"],
        speed_kts=v["speed_kts"],
        heading_deg=v["heading_deg"],
        lat=v["lat"],
        lon=v["lon"],
        last_ais_timestamp=v["last_ais_timestamp"],
        flag=v["flag"],
        destination=v["destination"],
        draught_m=v["draught_m"],
        length_m=v["length_m"],
        ais_status=v["ais_status"],
    )


def get_trajectory_points(vessel_id: str) -> list[TrajectoryPoint] | None:
    v = _VESSELS.get(vessel_id)
    if not v:
        return None
    return [
        TrajectoryPoint(
            lat=p[0],
            lon=p[1],
            timestamp=p[2],
            speed_kts=p[3],
            heading_deg=p[4],
        )
        for p in v["path"]
    ]


def correlation_candidates(
    vessel_ids: list[str] | None = None,
) -> list[VesselCorrelationCandidate]:
    ids = vessel_ids or list(_VESSELS.keys())
    out: list[VesselCorrelationCandidate] = []
    for vid in ids:
        v = _VESSELS.get(vid)
        if not v:
            continue
        out.append(
            VesselCorrelationCandidate(
                vessel_id=v["vessel_id"],
                vessel_name=v["name"],
                mmsi=v["mmsi"],
                spatial_overlap_score=v["spatial"],
                temporal_overlap_score=v["temporal"],
                distance_to_spill_km=v["distance_km"],
                matched=v["matched"],
                notes=v["notes"],
            )
        )
    out.sort(key=lambda c: (c.spatial_overlap_score + c.temporal_overlap_score) / 2, reverse=True)
    return out


def risk_scores(vessel_ids: list[str] | None = None) -> list[VesselRiskScore]:
    ids = vessel_ids or list(_VESSELS.keys())
    ranked: list[VesselRiskScore] = []
    for vid in ids:
        v = _VESSELS.get(vid)
        if not v:
            continue
        factors = [
            RiskFactor(
                name="spatial_overlap",
                weight=0.40,
                score=v["spatial"],
                detail=f"Distance to spill ~ {v['distance_km']} km",
            ),
            RiskFactor(
                name="temporal_overlap",
                weight=0.30,
                score=v["temporal"],
                detail="AIS presence within analysis window",
            ),
            RiskFactor(
                name="vessel_class_risk",
                weight=0.20,
                score=0.9 if "Tanker" in v["vessel_type"] else 0.4,
                detail=v["vessel_type"],
            ),
            RiskFactor(
                name="ais_integrity",
                weight=0.10,
                score=0.2 if v["mmsi"] == "UNKNOWN" else 0.85,
                detail="MMSI missing" if v["mmsi"] == "UNKNOWN" else "MMSI present",
            ),
        ]
        ranked.append(
            VesselRiskScore(
                vessel_id=v["vessel_id"],
                vessel_name=v["name"],
                mmsi=v["mmsi"],
                risk_score=v["risk"],
                risk_level=v["risk_level"],
                factors=factors,
                rationale=v["rationale"],
            )
        )
    ranked.sort(key=lambda r: r.risk_score, reverse=True)
    return ranked
