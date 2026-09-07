from fastapi import APIRouter

from backend.schemas.correlation import CorrelateRequest, CorrelateResponse
from backend.services import ais_service, correlation_engine, mock_sih

router = APIRouter(prefix="/api/v1", tags=["correlation"])


@router.post("/correlate", response_model=CorrelateResponse)
def correlate_spill_vessels(payload: CorrelateRequest) -> CorrelateResponse:
    """Spill–vessel spatial/temporal correlation (AIS tracks when available)."""
    spill_id = payload.spill_id or mock_sih.DEFAULT_SPILL_ID

    if ais_service.using_csv():
        vessel_ids = payload.vessel_ids or ais_service.list_vessel_ids()
        candidates = correlation_engine.correlate_vessels(
            vessel_ids,
            time_window_hours=payload.time_window_hours,
            footprint=mock_sih.SPILL_FOOTPRINT,
        )
        source = "AIS trajectories + spill footprint"
    else:
        candidates = mock_sih.correlation_candidates(payload.vessel_ids)
        source = "mock fallback (no AIS CSV)"

    top = next((c.vessel_id for c in candidates if c.matched), None)
    if top is None and candidates:
        top = candidates[0].vessel_id

    return CorrelateResponse(
        spill_id=spill_id,
        time_window_hours=payload.time_window_hours,
        candidates=candidates,
        top_match_vessel_id=top,
        message=(
            f"Correlation complete using {source}. "
            f"{sum(1 for c in candidates if c.matched)} vessel(s) matched."
        ),
    )
