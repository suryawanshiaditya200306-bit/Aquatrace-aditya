from typing import Optional

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
    footprint: SpillFootprint
    estimated_volume_m3: Optional[float] = None
    sensor: str = "Sentinel-1 (mock)"
    message: str
    image_id: Optional[str] = None
