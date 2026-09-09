from fastapi import APIRouter, HTTPException

from backend.schemas.risk import RiskScoreRequest, RiskScoreResponse
from backend.services import ais_service, mock_sih, risk_engine, spill_registry

router = APIRouter(prefix="/api/v1/risk", tags=["risk"])


@router.post("/score", response_model=RiskScoreResponse)
def score_culprit_risk(payload: RiskScoreRequest) -> RiskScoreResponse:
    """Culprit risk scoring from correlation + AIS anomalies (mock fallback)."""
    spill_id = payload.spill_id or mock_sih.DEFAULT_SPILL_ID
    registered = spill_registry.get(spill_id)

    if registered is not None and not registered.spill_detected:
        return RiskScoreResponse(
            spill_id=spill_id,
            ranked_vessels=[],
            primary_culprit_vessel_id=None,
            spill_source="registry",
            spill_detected=False,
            message=(
                "No spill detected for this spill_id; risk scoring skipped."
            ),
        )

    if registered is not None:
        footprint = registered.footprint
        observed_at = registered.observed_at
        spill_source = "registry"
        spill_detected = registered.spill_detected
        footprint_note = "registered spill footprint"
    else:
        footprint = mock_sih.SPILL_FOOTPRINT
        observed_at = None
        spill_source = "mock_default"
        spill_detected = None
        footprint_note = "default mock spill footprint"

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
            footprint=footprint,
            observed_at=observed_at,
        )
        source = f"AIS anomalies + spatial/temporal correlation ({footprint_note})"
    else:
        if payload.vessel_id and mock_sih.get_vessel(payload.vessel_id) is None:
            raise HTTPException(
                status_code=404,
                detail=f"Vessel '{payload.vessel_id}' not found.",
            )
        vessel_ids = [payload.vessel_id] if payload.vessel_id else None
        ranked = mock_sih.risk_scores(vessel_ids)
        source = f"mock vessel fallback (no AIS CSV); spill via {spill_source}"

    primary = ranked[0].vessel_id if ranked else None

    return RiskScoreResponse(
        spill_id=spill_id,
        ranked_vessels=ranked,
        primary_culprit_vessel_id=primary,
        spill_source=spill_source,
        spill_detected=spill_detected,
        message=(
            f"Risk scoring using {source}. "
            f"Primary culprit candidate: {primary or 'none'}."
        ),
    )
