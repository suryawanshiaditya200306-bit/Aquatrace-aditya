from typing import Optional

from pydantic import BaseModel, Field


class TrajectoryPoint(BaseModel):
    lat: float
    lon: float
    timestamp: str
    speed_kts: Optional[float] = None
    heading_deg: Optional[float] = None
    course_deg: Optional[float] = None


class TrajectoryResponse(BaseModel):
    status: str = "ok"
    vessel_id: str
    vessel_name: str
    mmsi: str
    points: list[TrajectoryPoint]
    track_hours: float = Field(description="Approximate duration covered by the track.")
    message: str = "AIS trajectory."
