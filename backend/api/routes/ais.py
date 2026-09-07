from fastapi import APIRouter, HTTPException

from backend.schemas.ais import (
    AisReloadResponse,
    AisStatusResponse,
    VesselAnomaliesResponse,
)
from backend.services import ais_service

router = APIRouter(prefix="/api/v1", tags=["ais"])


@router.get("/ais/status", response_model=AisStatusResponse)
def ais_status() -> AisStatusResponse:
    data = ais_service.status()
    return AisStatusResponse(**data)


@router.post("/ais/reload", response_model=AisReloadResponse)
def ais_reload() -> AisReloadResponse:
    ais_service.reload_ais()
    data = ais_service.status()
    return AisReloadResponse(
        status="ok",
        source=data["source"],
        csv_path=data["csv_path"],
        vessel_count=data["vessel_count"],
        record_count=data["record_count"],
        message=f"Reload complete. {data['message']}",
    )


@router.get("/vessels/{vessel_id}/anomalies", response_model=VesselAnomaliesResponse)
def vessel_anomalies(vessel_id: str) -> VesselAnomaliesResponse:
    """Detect sudden speed changes and sharp course changes on an AIS track."""
    if not ais_service.using_csv():
        raise HTTPException(
            status_code=503,
            detail=(
                "AIS CSV not loaded — anomalies require real AIS tracks. "
                "Place a CSV under data/ais/ or set AQUASLICK_AIS_CSV."
            ),
        )
    result = ais_service.detect_anomalies(vessel_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Vessel '{vessel_id}' not found in AIS data.")
    return VesselAnomaliesResponse(**result)
