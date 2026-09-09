from typing import Literal, Optional

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
    spill_source: Literal["registry", "mock_default"] = Field(
        default="mock_default",
        description=(
            "registry = footprint/time from in-memory spill analyze result; "
            "mock_default = fallback prototype spill geography."
        ),
    )
    spill_detected: Optional[bool] = Field(
        default=None,
        description=(
            "From registered analyze result when spill_source=registry; "
            "null for mock_default."
        ),
    )
    message: str
