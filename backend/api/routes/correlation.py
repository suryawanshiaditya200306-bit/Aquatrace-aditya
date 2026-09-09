from fastapi import APIRouter

from backend.schemas.correlation import CorrelateRequest, CorrelateResponse
from backend.services import ais_service, correlation_engine, mock_sih, spill_registry

router = APIRouter(prefix="/api/v1", tags=["correlation"])


@router.post("/correlate", response_model=CorrelateResponse)
def correlate_spill_vessels(payload: CorrelateRequest) -> CorrelateResponse:
    """Spill–vessel spatial/temporal correlation (AIS tracks when available)."""
    spill_id = payload.spill_id or mock_sih.DEFAULT_SPILL_ID
    registered = spill_registry.get(spill_id)

    if registered is not None:
        footprint = registered.footprint
        observed_at = registered.observed_at
        spill_source = "registry"
        footprint_note = "registered spill footprint"
    else:
        footprint = mock_sih.SPILL_FOOTPRINT
        observed_at = None
        spill_source = "mock_default"
        footprint_note = "default mock spill footprint"

    if ais_service.using_csv():
        vessel_ids = payload.vessel_ids or ais_service.list_vessel_ids()
        candidates = correlation_engine.correlate_vessels(
            vessel_ids,
            time_window_hours=payload.time_window_hours,
            footprint=footprint,
            observed_at=observed_at,
        )
        source = f"AIS trajectories + {footprint_note}"
    else:
        candidates = mock_sih.correlation_candidates(payload.vessel_ids)
        source = f"mock vessel fallback (no AIS CSV); spill via {spill_source}"

    top = next((c.vessel_id for c in candidates if c.matched), None)
    if top is None and candidates:
        top = candidates[0].vessel_id

    return CorrelateResponse(
        spill_id=spill_id,
        time_window_hours=payload.time_window_hours,
        candidates=candidates,
        top_match_vessel_id=top,
        spill_source=spill_source,
        message=(
            f"Correlation complete using {source}. "
            f"{sum(1 for c in candidates if c.matched)} vessel(s) matched."
        ),
    )
