"""Spill analysis route: multipart SAR upload or legacy JSON (mock-compatible)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from starlette.datastructures import UploadFile as StarletteUploadFile

from backend.schemas.spill import SpillAnalyzeRequest, SpillAnalyzeResponse
from backend.services import mock_sih, sar_model, spill_registry
from backend.services.uploads import UPLOAD_DIR, save_upload

router = APIRouter(prefix="/api/v1/spill", tags=["spill"])


def _resolve_uploaded_image(image_id: str) -> Path:
    """Locate a previously saved upload by image_id (any allowed extension)."""
    matches = list(UPLOAD_DIR.glob(f"{image_id}.*"))
    if not matches:
        raise HTTPException(
            status_code=404,
            detail=f"No uploaded image found for image_id '{image_id}'.",
        )
    return matches[0]


def _register_spill(
    response: SpillAnalyzeResponse,
    *,
    aoi_name: Optional[str] = None,
) -> SpillAnalyzeResponse:
    """Store successful analyze results for later /correlate lookup.

    Footprint may still be placeholder geography until SAR is georeferenced.
    Observation time is omitted (no reliable SAR acquisition metadata yet).
    """
    if response.status != "ok" or not response.spill_id:
        return response
    spill_registry.register(
        response.spill_id,
        response.footprint,
        observed_at=None,
        image_id=response.image_id,
        inference_mode=response.inference_mode,
        spill_detected=response.spill_detected,
        aoi_name=aoi_name,
    )
    return response


def _mock_response(
    *,
    aoi_name: Optional[str],
    image_id: Optional[str],
    reason: str,
) -> SpillAnalyzeResponse:
    return _register_spill(
        SpillAnalyzeResponse(
            status="ok",
            spill_id=mock_sih.DEFAULT_SPILL_ID,
            spill_detected=True,
            confidence=0.91,
            spill_area_pct=0.0,
            inference_time_ms=0.0,
            inference_mode="mock",
            spill_boundary=[],
            footprint=mock_sih.SPILL_FOOTPRINT,
            estimated_volume_m3=480.0,
            sensor="Sentinel-1 (mock)",
            message=f"Mock spill analysis for '{aoi_name or 'AOI'}'. {reason}",
            image_id=image_id,
        ),
        aoi_name=aoi_name,
    )


def _real_response(
    *,
    image_path: Path,
    image_id: str,
    aoi_name: Optional[str],
) -> SpillAnalyzeResponse:
    try:
        result = sar_model.run_sar_inference(image_path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        return _mock_response(
            aoi_name=aoi_name,
            image_id=image_id,
            reason=f"Falling back to mock: {exc}",
        )

    spill_detected = bool(result["spill_detected"])
    spill_boundary = result.get("spill_boundary") or []
    return _register_spill(
        SpillAnalyzeResponse(
            status="ok",
            spill_id=f"spill_{image_id[:12]}",
            spill_detected=spill_detected,
            confidence=float(result["confidence"]),
            spill_area_pct=float(result["spill_area_pct"]),
            inference_time_ms=float(result["inference_time_ms"]),
            inference_mode="real",
            spill_boundary=spill_boundary,
            footprint=mock_sih.SPILL_FOOTPRINT,
            estimated_volume_m3=480.0 if spill_detected else None,
            sensor="Sentinel-1 SAR (DeepLab)",
            message=(
                f"SAR DeepLab inference for '{aoi_name or 'AOI'}' "
                f"({result['inference_time_ms']} ms)."
            ),
            image_id=image_id,
        ),
        aoi_name=aoi_name,
    )


async def _analyze_from_image(
    *,
    image_path: Path,
    image_id: str,
    aoi_name: Optional[str],
) -> SpillAnalyzeResponse:
    if sar_model.get_detector() is None:
        return _mock_response(
            aoi_name=aoi_name,
            image_id=image_id,
            reason=(
                sar_model.get_load_error()
                or f"Model unavailable at {sar_model.resolve_model_path()}."
            ),
        )
    return _real_response(
        image_path=image_path, image_id=image_id, aoi_name=aoi_name
    )


@router.post("/analyze", response_model=SpillAnalyzeResponse)
async def analyze_spill(request: Request) -> SpillAnalyzeResponse:
    """
    Spill analysis.

    - ``multipart/form-data`` with ``file`` → real SARSpillDetector when available
    - ``application/json`` (legacy ``api_client``) → mock, or real via ``image_id``
    """
    content_type = (request.headers.get("content-type") or "").lower()

    if "multipart/form-data" in content_type:
        form = await request.form()
        aoi_raw = form.get("aoi_name")
        aoi_name = str(aoi_raw) if aoi_raw not in (None, "") else "East Coast Corridor"
        form_image_id = form.get("image_id")
        image_id = (
            str(form_image_id) if form_image_id not in (None, "") else None
        )

        upload = form.get("file")
        if isinstance(upload, StarletteUploadFile) and (
            upload.filename or upload.content_type
        ):
            saved_id, image_path = await save_upload(upload)
            return await _analyze_from_image(
                image_path=image_path,
                image_id=saved_id,
                aoi_name=aoi_name,
            )

        if image_id:
            path = _resolve_uploaded_image(image_id)
            return await _analyze_from_image(
                image_path=path, image_id=image_id, aoi_name=aoi_name
            )

        return _mock_response(
            aoi_name=aoi_name,
            image_id=None,
            reason=(
                "Multipart request without file or image_id. "
                "Using mock SIH analysis."
            ),
        )

    # JSON / empty / other — preserve api_client.analyze_spill() compatibility
    payload = SpillAnalyzeRequest()
    raw = await request.body()
    if raw.strip():
        try:
            payload = SpillAnalyzeRequest.model_validate(json.loads(raw))
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(
                status_code=400,
                detail=f"Invalid JSON body: {exc}",
            ) from exc

    aoi = payload.aoi_name
    img_id = payload.image_id

    if img_id:
        path = _resolve_uploaded_image(img_id)
        return await _analyze_from_image(
            image_path=path, image_id=img_id, aoi_name=aoi
        )

    if not sar_model.is_model_available():
        reason = (
            f"No image provided. Model file missing at "
            f"{sar_model.resolve_model_path()}. Using mock SIH analysis."
        )
    else:
        reason = (
            "No image provided (JSON body only). "
            "Upload multipart file or pass image_id from /predict. "
            "Using mock SIH analysis."
        )
    return _mock_response(aoi_name=aoi, image_id=img_id, reason=reason)
