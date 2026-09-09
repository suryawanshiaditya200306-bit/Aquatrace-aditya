"""Lazy singleton wrapper around aquatrace_sar_engine.SARSpillDetector.

TensorFlow and the .h5 weights are loaded on first use only, not at API import.
"""

from __future__ import annotations

import logging
import os
import sys
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from aquatrace_sar_engine import SARSpillDetector

logger = logging.getLogger(__name__)

# Project root: backend/services/sar_model.py → parents[2]
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_MODEL_PATH = _PROJECT_ROOT / "deeplab_final_model.h5"

# Ensure root aquatrace_sar_engine.py is importable regardless of CWD.
_root_str = str(_PROJECT_ROOT)
if _root_str not in sys.path:
    sys.path.insert(0, _root_str)

_lock = threading.Lock()
_detector: Optional["SARSpillDetector"] = None
_load_attempted = False
_load_error: Optional[str] = None


def resolve_model_path() -> Path:
    """Return model path from AQUASLICK_MODEL_PATH or the local default."""
    override = os.environ.get("AQUASLICK_MODEL_PATH", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return _DEFAULT_MODEL_PATH


def is_model_available() -> bool:
    """True if the weights file exists on disk (does not load TF)."""
    return resolve_model_path().is_file()


def get_load_error() -> Optional[str]:
    return _load_error


def get_detector() -> Optional["SARSpillDetector"]:
    """
    Return a process-wide SARSpillDetector, loading it once.

    Returns None when the model file is missing or load fails.
    """
    global _detector, _load_attempted, _load_error

    if _detector is not None:
        return _detector
    if _load_attempted and _detector is None:
        return None

    with _lock:
        if _detector is not None:
            return _detector
        if _load_attempted and _detector is None:
            return None

        _load_attempted = True
        model_path = resolve_model_path()
        if not model_path.is_file():
            _load_error = f"Model file not found at {model_path}"
            logger.warning(_load_error)
            return None

        try:
            # Import only when loading so API startup stays light.
            from aquatrace_sar_engine import SARSpillDetector

            logger.info("Loading SAR model from %s", model_path)
            _detector = SARSpillDetector(str(model_path))
            _load_error = None
            logger.info("SAR model loaded successfully")
        except Exception as exc:  # noqa: BLE001 — surface any load failure as unavailable
            _load_error = f"Failed to load SAR model: {exc}"
            logger.exception(_load_error)
            _detector = None

        return _detector


def run_sar_inference(image_path: Path) -> dict[str, Any]:
    """
    Run SARSpillDetector on a saved image.

    Returns detector dict with confidence normalized to 0-1 for API schemas.
    Raises FileNotFoundError / ValueError on bad inputs; RuntimeError if model unavailable.
    """
    detector = get_detector()
    if detector is None:
        raise RuntimeError(_load_error or "SAR model is not available")

    if not image_path.is_file():
        raise FileNotFoundError(f"Image not found at {image_path}")

    try:
        result = detector.predict(str(image_path))
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Invalid or unreadable image: {exc}") from exc

    # Import here so OpenCV is only needed when inference runs.
    from backend.services.mask_boundary import mask_to_normalized_boundary

    # Engine returns confidence on a 0-100 scale; API uses 0-1.
    confidence_pct = float(result["confidence"])
    spill_detected = bool(result["spill_detected"])
    spill_mask = result.get("spill_mask")

    # Boundary from existing mask only when a spill was detected; never georeference here.
    if spill_detected:
        spill_boundary = mask_to_normalized_boundary(spill_mask)
    else:
        spill_boundary = []

    result = dict(result)
    result["confidence"] = round(max(0.0, min(confidence_pct / 100.0, 1.0)), 4)
    result["spill_boundary"] = spill_boundary
    # Keep large arrays out of API JSON.
    result.pop("spill_mask", None)
    result.pop("anomaly_probability", None)
    return result
