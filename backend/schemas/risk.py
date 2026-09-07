from typing import Optional

from pydantic import BaseModel, Field


class RiskScoreRequest(BaseModel):
    spill_id: Optional[str] = None
    vessel_id: Optional[str] = Field(
        default=None,
        description="Score one vessel. If omitted, ranks all correlated candidates.",
    )


class RiskFactor(BaseModel):
    name: str
    weight: float = Field(ge=0.0, le=1.0)
    score: float = Field(ge=0.0, le=1.0)
    detail: str


class VesselRiskScore(BaseModel):
    vessel_id: str
    vessel_name: str
    mmsi: str
    risk_score: float = Field(ge=0.0, le=1.0)
    risk_level: str  # low | moderate | high | critical
    factors: list[RiskFactor]
    rationale: str


class RiskScoreResponse(BaseModel):
    status: str = "ok"
    spill_id: str
    ranked_vessels: list[VesselRiskScore]
    primary_culprit_vessel_id: Optional[str] = None
    message: str
