"""In-memory spill registry for analyze → correlate plumbing.

Stores spill footprints (and optional observation time) keyed by spill_id.
No database — process-local only. Geography may still be placeholder until
SAR imagery is georeferenced.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from backend.schemas.spill import SpillFootprint

_lock = threading.Lock()
_REGISTRY: dict[str, "RegisteredSpill"] = {}


@dataclass
class RegisteredSpill:
    spill_id: str
    footprint: SpillFootprint
    observed_at: Optional[datetime] = None
    image_id: Optional[str] = None
    inference_mode: Optional[str] = None
    spill_detected: bool = False
    aoi_name: Optional[str] = None
    registered_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


def register(
    spill_id: str,
    footprint: SpillFootprint,
    *,
    observed_at: Optional[datetime] = None,
    image_id: Optional[str] = None,
    inference_mode: Optional[str] = None,
    spill_detected: bool = False,
    aoi_name: Optional[str] = None,
) -> RegisteredSpill:
    """Upsert a spill record. Returns the stored record."""
    record = RegisteredSpill(
        spill_id=spill_id,
        footprint=footprint.model_copy(deep=True),
        observed_at=observed_at,
        image_id=image_id,
        inference_mode=inference_mode,
        spill_detected=spill_detected,
        aoi_name=aoi_name,
    )
    with _lock:
        _REGISTRY[spill_id] = record
    return record


def get(spill_id: str) -> Optional[RegisteredSpill]:
    with _lock:
        return _REGISTRY.get(spill_id)


def clear() -> None:
    """Drop all registered spills (tests / local reset)."""
    with _lock:
        _REGISTRY.clear()


def count() -> int:
    with _lock:
        return len(_REGISTRY)
