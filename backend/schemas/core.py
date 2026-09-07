from typing import Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "aquaslick-api"


class StatusResponse(BaseModel):
    status: str = "ready"
    version: str = "0.1.0"
    detection_model: str = "not_loaded"
    message: str = "AquaSlick API is running. Detection pipeline not wired yet."


class PredictResponse(BaseModel):
    status: str = "ok"
    spill_detected: bool = False
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    message: str
    image_id: Optional[str] = None
