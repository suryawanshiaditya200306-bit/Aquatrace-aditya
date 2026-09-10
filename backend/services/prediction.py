"""Oil-spill prediction service — wires SARSpillDetector when available."""

from __future__ import annotations

from pathlib import Path

from backend.schemas import PredictResponse
from backend.services import sar_model


def run_prediction(image_path: Path, image_id: str) -> PredictResponse:
    """Run spill detection on a saved image (real model or clear stub)."""
    if not image_path.is_file():
        return PredictResponse(
            status="error",
            spill_detected=False,
            confidence=0.0,
            message=f"Image not found at {image_path}",
            image_id=image_id,
        )

    if sar_model.get_detector() is None:
        detail = sar_model.get_load_error() or (
            "Detection model is not available "
            f"(expected at {sar_model.resolve_model_path()})."
        )
        return PredictResponse(
            status="ok",
            spill_detected=False,
            confidence=0.0,
            message=f"Image received and stored. Mock/unavailable: {detail}",
            image_id=image_id,
        )

    try:
        result = sar_model.run_sar_inference(image_path)
    except ValueError as exc:
        return PredictResponse(
            status="error",
            spill_detected=False,
            confidence=0.0,
            message=str(exc),
            image_id=image_id,
        )
    except RuntimeError as exc:
        return PredictResponse(
            status="ok",
            spill_detected=False,
            confidence=0.0,
            message=f"Model unavailable: {exc}",
            image_id=image_id,
        )

    return PredictResponse(
        status="ok",
        spill_detected=bool(result["spill_detected"]),
        confidence=float(result["confidence"]),
        message=(
            f"SAR DeepLab inference in {result['inference_time_ms']} ms; "
            f"spill_area_pct={result['spill_area_pct']}"
        ),
        image_id=image_id,
    )
