from fastapi import APIRouter

from backend.schemas.spill import SpillAnalyzeRequest, SpillAnalyzeResponse
from backend.services import mock_sih

router = APIRouter(prefix="/api/v1/spill", tags=["spill"])


@router.post("/analyze", response_model=SpillAnalyzeResponse)
def analyze_spill(payload: SpillAnalyzeRequest) -> SpillAnalyzeResponse:
    """Placeholder spill analysis for the SIH workflow (no ML yet)."""
    return SpillAnalyzeResponse(
        spill_id=mock_sih.DEFAULT_SPILL_ID,
        spill_detected=True,
        confidence=0.91,
        footprint=mock_sih.SPILL_FOOTPRINT,
        estimated_volume_m3=480.0,
        message=(
            f"Mock spill analysis for '{payload.aoi_name or 'AOI'}'. "
            "Detection model not integrated yet."
        ),
        image_id=payload.image_id,
    )
