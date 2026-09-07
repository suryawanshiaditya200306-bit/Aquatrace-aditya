from fastapi import APIRouter, HTTPException

from backend.schemas.trajectory import TrajectoryResponse
from backend.services import ais_service, mock_sih

router = APIRouter(prefix="/api/v1/vessels", tags=["trajectory"])


@router.get("/{vessel_id}/trajectory", response_model=TrajectoryResponse)
def get_trajectory(vessel_id: str) -> TrajectoryResponse:
    """Historical AIS track from CSV, with mock fallback."""
    if ais_service.using_csv():
        data = ais_service.get_trajectory(vessel_id)
        if data is None:
            raise HTTPException(status_code=404, detail=f"Vessel '{vessel_id}' not found.")
        return TrajectoryResponse(**data)

    vessel = mock_sih.get_vessel(vessel_id)
    points = mock_sih.get_trajectory_points(vessel_id)
    if vessel is None or points is None:
        raise HTTPException(status_code=404, detail=f"Vessel '{vessel_id}' not found.")

    return TrajectoryResponse(
        vessel_id=vessel_id,
        vessel_name=vessel["name"],
        mmsi=vessel["mmsi"],
        points=points,
        track_hours=8.0,
        message="Mock AIS trajectory placeholder.",
    )
