from typing import Literal, Optional

from pydantic import BaseModel, Field


class GeoPoint(BaseModel):
    lat: float
    lon: float


class SpillAnalyzeRequest(BaseModel):
    image_id: Optional[str] = Field(
        default=None,
        description="Optional id from a prior /predict upload.",
    )
    aoi_name: Optional[str] = Field(
        default="East Coast Corridor",
        description="Named area of interest for mock analysis.",
    )


class SpillFootprint(BaseModel):
    polygon: list[GeoPoint]
    centroid: GeoPoint
    area_sq_km: float


class SpillAnalyzeResponse(BaseModel):
    status: str = "ok"
    spill_id: str
    spill_detected: bool
    confidence: float = Field(ge=0.0, le=1.0)
    spill_area_pct: float = Field(default=0.0, ge=0.0, le=100.0)
    inference_time_ms: float = Field(default=0.0, ge=0.0)
    inference_mode: Literal["real", "mock"] = "mock"
    spill_boundary: list[list[float]] = Field(
        default_factory=list,
        description=(
            "Outer spill mask boundary in normalized image coordinates "
            "[[x, y], ...] with x,y in [0,1]. Empty when no spill."
        ),
    )
    footprint: SpillFootprint
    estimated_volume_m3: Optional[float] = None
    sensor: str = "Sentinel-1 (mock)"
    message: str
    image_id: Optional[str] = None
