"""Minimal HTTP client for the AquaSlick FastAPI backend."""

from __future__ import annotations

import os
from typing import Any, Optional

import requests

DEFAULT_API_BASE = os.getenv("AQUASLICK_API_BASE", "http://127.0.0.1:8000")
TIMEOUT_SECONDS = 5


class BackendError(Exception):
    """Raised when the FastAPI backend cannot be reached or returns an error."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def _url(path: str, base_url: str = DEFAULT_API_BASE) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def _request(
    method: str,
    path: str,
    *,
    json_body: Optional[dict[str, Any]] = None,
    base_url: str = DEFAULT_API_BASE,
) -> Any:
    try:
        response = requests.request(
            method,
            _url(path, base_url),
            json=json_body,
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError as exc:
        raise BackendError(
            "Backend unavailable — cannot connect to AquaSlick API. "
            "Start it with: python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000"
        ) from exc
    except requests.exceptions.Timeout as exc:
        raise BackendError("Backend request timed out. Try again in a moment.") from exc
    except requests.exceptions.HTTPError as exc:
        detail = ""
        try:
            detail = exc.response.json().get("detail", exc.response.text)
        except Exception:
            detail = getattr(exc.response, "text", str(exc))
        raise BackendError(f"Backend error ({exc.response.status_code}): {detail}") from exc
    except requests.exceptions.RequestException as exc:
        raise BackendError(f"Backend request failed: {exc}") from exc


def get_health(base_url: str = DEFAULT_API_BASE) -> dict[str, Any]:
    return _request("GET", "/health", base_url=base_url)


def get_vessels(base_url: str = DEFAULT_API_BASE) -> list[dict[str, Any]]:
    data = _request("GET", "/api/v1/vessels", base_url=base_url)
    return data.get("vessels", [])


def get_vessel(vessel_id: str, base_url: str = DEFAULT_API_BASE) -> dict[str, Any]:
    return _request("GET", f"/api/v1/vessels/{vessel_id}", base_url=base_url)


def get_trajectory(vessel_id: str, base_url: str = DEFAULT_API_BASE) -> dict[str, Any]:
    return _request("GET", f"/api/v1/vessels/{vessel_id}/trajectory", base_url=base_url)


def analyze_spill(base_url: str = DEFAULT_API_BASE) -> dict[str, Any]:
    return _request("POST", "/api/v1/spill/analyze", json_body={}, base_url=base_url)


def correlate_vessel(
    vessel_id: str,
    *,
    time_window_hours: float = 12.0,
    base_url: str = DEFAULT_API_BASE,
) -> dict[str, Any]:
    return _request(
        "POST",
        "/api/v1/correlate",
        json_body={"vessel_ids": [vessel_id], "time_window_hours": time_window_hours},
        base_url=base_url,
    )


def score_risk(
    vessel_id: str,
    *,
    base_url: str = DEFAULT_API_BASE,
) -> dict[str, Any]:
    return _request(
        "POST",
        "/api/v1/risk/score",
        json_body={"vessel_id": vessel_id},
        base_url=base_url,
    )
