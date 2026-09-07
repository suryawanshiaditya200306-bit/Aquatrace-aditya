from fastapi import APIRouter, HTTPException

from backend.schemas.risk import RiskScoreRequest, RiskScoreResponse
from backend.services import ais_service, mock_sih, risk_engine

router = APIRouter(prefix="/api/v1/risk", tags=["risk"])


@router.post("/score", response_model=RiskScoreResponse)
def score_culprit_risk(payload: RiskScoreRequest) -> RiskScoreResponse:
    """Culprit risk scoring from correlation + AIS anomalies (mock fallback)."""
    spill_id = payload.spill_id or mock_sih.DEFAULT_SPILL_ID

    if ais_service.using_csv():
        if payload.vessel_id:
            if ais_service.get_vessel_detail(payload.vessel_id) is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Vessel '{payload.vessel_id}' not found.",
                )
            vessel_ids = [payload.vessel_id]
        else:
            vessel_ids = ais_service.list_vessel_ids()

        ranked = risk_engine.score_vessels(
            vessel_ids,
            footprint=mock_sih.SPILL_FOOTPRINT,
        )
        source = "AIS anomalies + spatial/temporal correlation"
    else:
        if payload.vessel_id and mock_sih.get_vessel(payload.vessel_id) is None:
            raise HTTPException(
                status_code=404,
                detail=f"Vessel '{payload.vessel_id}' not found.",
            )
        vessel_ids = [payload.vessel_id] if payload.vessel_id else None
        ranked = mock_sih.risk_scores(vessel_ids)
        source = "mock fallback (no AIS CSV)"

    primary = ranked[0].vessel_id if ranked else None

    return RiskScoreResponse(
        spill_id=spill_id,
        ranked_vessels=ranked,
        primary_culprit_vessel_id=primary,
        message=(
            f"Risk scoring using {source}. "
            f"Primary culprit candidate: {primary or 'none'}."
        ),
    )
