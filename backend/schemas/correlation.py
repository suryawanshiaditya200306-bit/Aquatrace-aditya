from typing import Optional

from pydantic import BaseModel, Field


class CorrelateRequest(BaseModel):
    spill_id: Optional[str] = Field(
        default=None,
        description="Spill id from /spill/analyze. Uses default mock spill if omitted.",
    )
    vessel_ids: Optional[list[str]] = Field(
        default=None,
        description="Optional vessel filter. Defaults to all mock vessels in AOI.",
    )
    time_window_hours: float = Field(default=12.0, ge=0.5, le=168.0)


class VesselCorrelationCandidate(BaseModel):
    vessel_id: str
    vessel_name: str
    mmsi: str
    spatial_overlap_score: float = Field(ge=0.0, le=1.0)
    temporal_overlap_score: float = Field(ge=0.0, le=1.0)
    distance_to_spill_km: float
    matched: bool
    notes: str


class CorrelateResponse(BaseModel):
    status: str = "ok"
    spill_id: str
    time_window_hours: float
    candidates: list[VesselCorrelationCandidate]
    top_match_vessel_id: Optional[str] = None
    message: str
