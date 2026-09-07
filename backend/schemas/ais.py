from typing import Any, Optional

from pydantic import BaseModel, Field


class AisStatusResponse(BaseModel):
    status: str = "ok"
    source: str  # csv | mock
    csv_path: Optional[str] = None
    vessel_count: int = 0
    record_count: int = 0
    message: str


class AisReloadResponse(BaseModel):
    status: str = "ok"
    source: str
    csv_path: Optional[str] = None
    vessel_count: int = 0
    record_count: int = 0
    message: str


class VesselAnomaly(BaseModel):
    type: str
    timestamp: str
    lat: float
    lon: float
    magnitude: float
    unit: str
    detail: str


class VesselAnomaliesResponse(BaseModel):
    status: str = "ok"
    vessel_id: str
    vessel_name: str
    mmsi: str
    anomaly_count: int
    anomalies: list[VesselAnomaly]
    thresholds: dict[str, Any] = Field(default_factory=dict)
    message: str
