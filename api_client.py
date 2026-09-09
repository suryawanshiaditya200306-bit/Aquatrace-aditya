"""Minimal HTTP client for the AquaSlick FastAPI backend."""

from __future__ import annotations

import os
from typing import Any, BinaryIO, Optional, Union

import requests

DEFAULT_API_BASE = os.getenv("AQUASLICK_API_BASE", "http://127.0.0.1:8000")
# Short calls (vessels, correlate, risk) — still generous for local prototypes.
TIMEOUT_SECONDS = 30
# DeepLab inference on first load can take well over a minute.
ANALYZE_TIMEOUT_SECONDS = 300

FileSource = Union[str, bytes, BinaryIO]


class BackendError(Exception):
    """Raised when the FastAPI backend cannot be reached or returns an error."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def _url(path: str, base_url: str = DEFAULT_API_BASE) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def _raise_from_requests(exc: Exception) -> None:
    if isinstance(exc, requests.exceptions.ConnectionError):
        raise BackendError(
            "Backend unavailable — cannot connect to AquaSlick API. "
            "Start it with: python -m uvicorn backend.main:app --reload "
            "--host 127.0.0.1 --port 8000"
        ) from exc
    if isinstance(exc, requests.exceptions.Timeout):
        raise BackendError("Backend request timed out. Try again in a moment.") from exc
    if isinstance(exc, requests.exceptions.HTTPError):
        detail = ""
        try:
            detail = exc.response.json().get("detail", exc.response.text)
        except Exception:
            detail = getattr(exc.response, "text", str(exc))
        raise BackendError(
            f"Backend error ({exc.response.status_code}): {detail}"
        ) from exc
    if isinstance(exc, requests.exceptions.RequestException):
        raise BackendError(f"Backend request failed: {exc}") from exc
    raise exc


def _request(
    method: str,
    path: str,
    *,
    json_body: Optional[dict[str, Any]] = None,
    files: Optional[dict[str, Any]] = None,
    data: Optional[dict[str, Any]] = None,
    base_url: str = DEFAULT_API_BASE,
    timeout: float = TIMEOUT_SECONDS,
) -> Any:
    try:
        response = requests.request(
            method,
            _url(path, base_url),
            json=json_body if files is None else None,
            files=files,
            data=data,
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as exc:
        _raise_from_requests(exc)


def get_health(base_url: str = DEFAULT_API_BASE) -> dict[str, Any]:
    return _request("GET", "/health", base_url=base_url)


def get_vessels(base_url: str = DEFAULT_API_BASE) -> list[dict[str, Any]]:
    data = _request("GET", "/api/v1/vessels", base_url=base_url)
    return data.get("vessels", [])


def get_vessel(vessel_id: str, base_url: str = DEFAULT_API_BASE) -> dict[str, Any]:
    return _request("GET", f"/api/v1/vessels/{vessel_id}", base_url=base_url)


def get_trajectory(vessel_id: str, base_url: str = DEFAULT_API_BASE) -> dict[str, Any]:
    return _request("GET", f"/api/v1/vessels/{vessel_id}/trajectory", base_url=base_url)


def analyze_spill(
    image: Optional[FileSource] = None,
    *,
    filename: Optional[str] = None,
    content_type: Optional[str] = None,
    base_url: str = DEFAULT_API_BASE,
) -> dict[str, Any]:
    """
    POST /api/v1/spill/analyze.

    - With ``image``: multipart upload (real SAR / DeepLab path when model is loaded).
    - Without ``image``: empty JSON body (legacy mock / default footprint path).
    """
    if image is None:
        return _request(
            "POST",
            "/api/v1/spill/analyze",
            json_body={},
            base_url=base_url,
            timeout=TIMEOUT_SECONDS,
        )

    name = filename or "sar_image.png"
    mime = content_type or "application/octet-stream"

    if isinstance(image, (bytes, bytearray)):
        file_tuple = (name, bytes(image), mime)
    elif isinstance(image, str):
        file_tuple = (name, open(image, "rb"), mime)  # noqa: SIM115 — closed below
    else:
        # file-like (e.g. Streamlit UploadedFile)
        raw = image.read() if hasattr(image, "read") else image
        if hasattr(image, "seek"):
            try:
                image.seek(0)
            except Exception:
                pass
        file_tuple = (name, raw, mime)

    try:
        return _request(
            "POST",
            "/api/v1/spill/analyze",
            files={"file": file_tuple},
            base_url=base_url,
            timeout=ANALYZE_TIMEOUT_SECONDS,
        )
    finally:
        # Close path-opened handles only
        handle = file_tuple[1]
        if isinstance(image, str) and hasattr(handle, "close"):
            handle.close()


def correlate_vessel(
    vessel_id: str,
    *,
    spill_id: Optional[str] = None,
    time_window_hours: float = 12.0,
    base_url: str = DEFAULT_API_BASE,
) -> dict[str, Any]:
    """POST /api/v1/correlate — backend filter field is ``vessel_ids`` (list)."""
    body: dict[str, Any] = {
        "vessel_ids": [vessel_id],
        "time_window_hours": time_window_hours,
    }
    if spill_id:
        body["spill_id"] = spill_id
    return _request(
        "POST",
        "/api/v1/correlate",
        json_body=body,
        base_url=base_url,
    )


def score_risk(
    vessel_id: str,
    *,
    spill_id: Optional[str] = None,
    base_url: str = DEFAULT_API_BASE,
) -> dict[str, Any]:
    body: dict[str, Any] = {"vessel_id": vessel_id}
    if spill_id:
        body["spill_id"] = spill_id
    return _request(
        "POST",
        "/api/v1/risk/score",
        json_body=body,
        base_url=base_url,
    )
