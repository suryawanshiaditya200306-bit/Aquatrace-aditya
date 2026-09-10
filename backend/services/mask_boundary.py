"""Convert a binary spill mask to a normalized image-space polygon.

Coordinates are in the model input frame (typically 256x256), scaled to 0-1.
x = column / width, y = row / height. Not geographic.
"""

from __future__ import annotations

from typing import Any

import cv2
import numpy as np


def mask_to_normalized_boundary(
    spill_mask: Any,
    *,
    max_points: int = 200,
) -> list[list[float]]:
    """
    Return the outer boundary of ``spill_mask`` as ``[[x, y], ...]`` in [0, 1].

    Empty / all-false masks return ``[]``. On contour failure, returns ``[]``.
    """
    if spill_mask is None:
        return []

    mask = np.asarray(spill_mask)
    if mask.ndim != 2 or mask.size == 0 or not np.any(mask):
        return []

    height, width = int(mask.shape[0]), int(mask.shape[1])
    if height <= 0 or width <= 0:
        return []

    binary = (mask.astype(np.uint8) * 255)
    contours, _ = cv2.findContours(
        binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    if not contours:
        return []

    # Outer boundary of the primary (largest) connected component.
    contour = max(contours, key=cv2.contourArea)
    if cv2.contourArea(contour) <= 0:
        return []

    peri = cv2.arcLength(contour, closed=True)
    epsilon = max(0.5, 0.002 * peri)
    approx = cv2.approxPolyDP(contour, epsilon, closed=True)

    # If still too dense, resample by stride so the JSON stays frontend-friendly.
    pts = approx.reshape(-1, 2)
    if len(pts) > max_points:
        step = int(np.ceil(len(pts) / max_points))
        pts = pts[::step]

    if len(pts) < 3:
        return []

    boundary: list[list[float]] = []
    for x_px, y_px in pts:
        x_n = round(float(x_px) / width, 6)
        y_n = round(float(y_px) / height, 6)
        boundary.append(
            [
                max(0.0, min(x_n, 1.0)),
                max(0.0, min(y_n, 1.0)),
            ]
        )
    return boundary
