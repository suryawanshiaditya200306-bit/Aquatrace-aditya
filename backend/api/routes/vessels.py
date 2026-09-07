from fastapi import APIRouter, HTTPException

from backend.schemas.vessels import VesselDetailResponse, VesselListResponse
from backend.services import ais_service, mock_sih

router = APIRouter(prefix="/api/v1/vessels", tags=["vessels"])


@router.get("", response_model=VesselListResponse)
def list_vessels() -> VesselListResponse:
    """List vessels from local AIS CSV, with mock fallback."""
    if ais_service.using_csv():
        vessels = ais_service.list_vessel_summaries()
        return VesselListResponse(
            count=len(vessels),
            vessels=vessels,
            message="Vessels derived from local AIS CSV.",
        )

    vessels = mock_sih.list_vessel_summaries()
    return VesselListResponse(
        count=len(vessels),
        vessels=vessels,
        message="Mock AIS snapshot (no CSV found under data/ais/).",
    )


@router.get("/{vessel_id}", response_model=VesselDetailResponse)
def get_vessel(vessel_id: str) -> VesselDetailResponse:
    if ais_service.using_csv():
        detail = ais_service.get_vessel_detail(vessel_id)
        if detail is None:
            raise HTTPException(status_code=404, detail=f"Vessel '{vessel_id}' not found.")
        return detail

    detail = mock_sih.get_vessel_detail(vessel_id)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"Vessel '{vessel_id}' not found.")
    return detail
