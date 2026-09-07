"""Public Pydantic schemas for the AquaSlick API."""

from backend.schemas.ais import (
    AisReloadResponse,
    AisStatusResponse,
    VesselAnomaliesResponse,
    VesselAnomaly,
)
from backend.schemas.core import HealthResponse, PredictResponse, StatusResponse
from backend.schemas.correlation import (
    CorrelateRequest,
    CorrelateResponse,
    VesselCorrelationCandidate,
)
from backend.schemas.risk import (
    RiskFactor,
    RiskScoreRequest,
    RiskScoreResponse,
    VesselRiskScore,
)
from backend.schemas.spill import (
    GeoPoint,
    SpillAnalyzeRequest,
    SpillAnalyzeResponse,
    SpillFootprint,
)
from backend.schemas.trajectory import TrajectoryPoint, TrajectoryResponse
from backend.schemas.vessels import (
    VesselDetailResponse,
    VesselListResponse,
    VesselSummary,
)

__all__ = [
    "HealthResponse",
    "StatusResponse",
    "PredictResponse",
    "GeoPoint",
    "SpillAnalyzeRequest",
    "SpillAnalyzeResponse",
    "SpillFootprint",
    "VesselSummary",
    "VesselListResponse",
    "VesselDetailResponse",
    "TrajectoryPoint",
    "TrajectoryResponse",
    "CorrelateRequest",
    "CorrelateResponse",
    "VesselCorrelationCandidate",
    "RiskScoreRequest",
    "RiskScoreResponse",
    "VesselRiskScore",
    "RiskFactor",
    "AisStatusResponse",
    "AisReloadResponse",
    "VesselAnomaly",
    "VesselAnomaliesResponse",
]
