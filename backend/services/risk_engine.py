"""Explainable culprit risk scoring from correlation + AIS anomalies."""

from __future__ import annotations

from typing import Optional

from backend.schemas.correlation import VesselCorrelationCandidate
from backend.schemas.risk import RiskFactor, VesselRiskScore
from backend.schemas.spill import SpillFootprint
from backend.services import ais_service, correlation_engine, mock_sih

# Weights must sum to 1.0
WEIGHTS = {
    "spatial_correlation": 0.25,
    "temporal_correlation": 0.20,
    "ais_anomaly_count": 0.20,
    "sudden_speed_changes": 0.15,
    "sharp_course_changes": 0.20,
}


def _risk_level(score: float) -> str:
    if score >= 0.85:
        return "critical"
    if score >= 0.65:
        return "high"
    if score >= 0.40:
        return "moderate"
    return "low"


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def score_vessel(
    vessel_id: str,
    *,
    correlation: Optional[VesselCorrelationCandidate] = None,
    time_window_hours: float = 12.0,
    footprint: Optional[SpillFootprint] = None,
) -> Optional[VesselRiskScore]:
    detail = ais_service.get_vessel_detail(vessel_id)
    if detail is None:
        return None

    if correlation is None:
        correlation = correlation_engine.correlate_vessel(
            vessel_id,
            footprint=footprint or mock_sih.SPILL_FOOTPRINT,
            time_window_hours=time_window_hours,
        )
    if correlation is None:
        return None

    anomaly_payload = ais_service.detect_anomalies(vessel_id) or {
        "anomaly_count": 0,
        "anomalies": [],
    }
    anomalies = anomaly_payload.get("anomalies", [])
    speed_n = sum(1 for a in anomalies if a.get("type") == "sudden_speed_change")
    course_n = sum(1 for a in anomalies if a.get("type") == "sharp_course_change")
    total_n = int(anomaly_payload.get("anomaly_count", len(anomalies)))

    spatial = _clamp01(correlation.spatial_overlap_score)
    temporal = _clamp01(correlation.temporal_overlap_score)
    # Saturate anomaly contributions for prototype explainability
    anomaly_score = _clamp01(total_n / 4.0)
    speed_score = _clamp01(speed_n / 2.0)
    course_score = _clamp01(course_n / 2.0)

    factors = [
        RiskFactor(
            name="spatial_correlation",
            weight=WEIGHTS["spatial_correlation"],
            score=round(spatial, 3),
            detail=f"Min distance to spill ~ {correlation.distance_to_spill_km} km",
        ),
        RiskFactor(
            name="temporal_correlation",
            weight=WEIGHTS["temporal_correlation"],
            score=round(temporal, 3),
            detail=correlation.notes,
        ),
        RiskFactor(
            name="ais_anomaly_count",
            weight=WEIGHTS["ais_anomaly_count"],
            score=round(anomaly_score, 3),
            detail=f"{total_n} AIS anomal{'y' if total_n == 1 else 'ies'} on track",
        ),
        RiskFactor(
            name="sudden_speed_changes",
            weight=WEIGHTS["sudden_speed_changes"],
            score=round(speed_score, 3),
            detail=f"{speed_n} sudden SOG change event(s)",
        ),
        RiskFactor(
            name="sharp_course_changes",
            weight=WEIGHTS["sharp_course_changes"],
            score=round(course_score, 3),
            detail=f"{course_n} sharp course change event(s)",
        ),
    ]

    risk_score = round(
        sum(f.weight * f.score for f in factors),
        3,
    )
    level = _risk_level(risk_score)

    rationale = (
        f"Risk {risk_score:.2f} ({level}) from spatial={spatial:.2f}, "
        f"temporal={temporal:.2f}, anomalies={total_n} "
        f"(speed={speed_n}, course={course_n})."
    )

    return VesselRiskScore(
        vessel_id=vessel_id,
        vessel_name=detail.name,
        mmsi=detail.mmsi,
        risk_score=risk_score,
        risk_level=level,
        factors=factors,
        rationale=rationale,
    )


def score_vessels(
    vessel_ids: Optional[list[str]] = None,
    *,
    time_window_hours: float = 12.0,
    footprint: Optional[SpillFootprint] = None,
) -> list[VesselRiskScore]:
    ids = vessel_ids or ais_service.list_vessel_ids()
    fp = footprint or mock_sih.SPILL_FOOTPRINT

    # Compute correlation once per vessel for consistent factors
    corr_map = {
        c.vessel_id: c
        for c in correlation_engine.correlate_vessels(
            ids,
            time_window_hours=time_window_hours,
            footprint=fp,
        )
    }

    ranked: list[VesselRiskScore] = []
    for vid in ids:
        scored = score_vessel(
            vid,
            correlation=corr_map.get(vid),
            time_window_hours=time_window_hours,
            footprint=fp,
        )
        if scored is not None:
            ranked.append(scored)

    ranked.sort(key=lambda r: r.risk_score, reverse=True)
    return ranked
