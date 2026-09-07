from typing import Optional

from pydantic import BaseModel, Field


class VesselSummary(BaseModel):
    vessel_id: str
    name: str
    mmsi: str
    vessel_type: str
    speed_kts: float
    heading_deg: float
    lat: float
    lon: float
    last_ais_timestamp: str
    flag: Optional[str] = None


class VesselListResponse(BaseModel):
    status: str = "ok"
    count: int
    vessels: list[VesselSummary]
    message: str = "Mock AIS snapshot for the East Coast corridor."


class VesselDetailResponse(VesselSummary):
    status: str = "ok"
    destination: Optional[str] = None
    draught_m: Optional[float] = None
    length_m: Optional[float] = None
    ais_status: str = "under_way"
    message: str = "Mock vessel detail from AIS placeholder."
