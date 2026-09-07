"""Oil-spill prediction service.

Inference is intentionally a stub so a classical CV or ML model can be
plugged in later without changing the API route.
"""

from __future__ import annotations

from pathlib import Path

from backend.schemas import PredictResponse


def run_prediction(image_path: Path, image_id: str) -> PredictResponse:
    """
    Run spill detection on a saved image.

    TODO(MODEL): Replace `_placeholder_inference` with the real pipeline
    (e.g. adaptive thresholding + morphology on SAR imagery).
    """
    if not image_path.is_file():
        return PredictResponse(
            status="error",
            spill_detected=False,
            confidence=0.0,
            message=f"Image not found at {image_path}",
            image_id=image_id,
        )

    spill_detected, confidence, detail = _placeholder_inference(image_path)

    return PredictResponse(
        status="ok",
        spill_detected=spill_detected,
        confidence=confidence,
        message=detail,
        image_id=image_id,
    )


# ---------------------------------------------------------------------------
# MODEL PLACEHOLDER — swap this function for real detection logic later.
# ---------------------------------------------------------------------------
def _placeholder_inference(image_path: Path) -> tuple[bool, float, str]:
    """
    Placeholder inference.

    Returns:
        spill_detected, confidence, message
    """
    _ = image_path  # will be used by the real model
    return (
        False,
        0.0,
        (
            "Image received and stored. Detection model is not integrated yet "
            "(placeholder inference)."
        ),
    )
