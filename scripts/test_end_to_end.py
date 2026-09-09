#!/usr/bin/env python3
"""AquaTrace backend end-to-end smoke test.

Calls:
  POST /api/v1/spill/analyze  (multipart SAR image)
  POST /api/v1/correlate      (spill_id + 12h window)
  POST /api/v1/risk/score     (same spill_id)

Uses only the Python standard library (urllib).
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import sys
import uuid
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "http://127.0.0.1:8000"
CORRELATE_WINDOW_HOURS = 12.0


def _die(message: str, code: int = 1) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)


def _pretty(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)


def _request_json(
    method: str,
    url: str,
    *,
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 300.0,
) -> dict[str, Any]:
    req = Request(url, data=data, method=method)
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    try:
        with urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            if not body.strip():
                return {}
            return json.loads(body)
    except HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP {exc.code} from {url}", file=sys.stderr)
        print(err_body or "(empty body)", file=sys.stderr)
        raise SystemExit(1) from exc
    except URLError as exc:
        _die(f"Could not reach API at {url}: {exc.reason}")
    except json.JSONDecodeError as exc:
        _die(f"Invalid JSON from {url}: {exc}")


def _multipart_file_body(
    field_name: str,
    file_path: Path,
) -> tuple[bytes, str]:
    boundary = f"----AquaTraceBoundary{uuid.uuid4().hex}"
    content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
    filename = file_path.name
    raw = file_path.read_bytes()

    lines = [
        f"--{boundary}".encode(),
        (
            f'Content-Disposition: form-data; name="{field_name}"; '
            f'filename="{filename}"'
        ).encode(),
        f"Content-Type: {content_type}".encode(),
        b"",
        raw,
        f"--{boundary}--".encode(),
        b"",
    ]
    body = b"\r\n".join(lines)
    header_value = f"multipart/form-data; boundary={boundary}"
    return body, header_value


def analyze_spill(base_url: str, image_path: Path) -> dict[str, Any]:
    url = f"{base_url.rstrip('/')}/api/v1/spill/analyze"
    body, content_type = _multipart_file_body("file", image_path)
    return _request_json(
        "POST",
        url,
        data=body,
        headers={"Content-Type": content_type},
    )


def correlate_spill(base_url: str, spill_id: str) -> dict[str, Any]:
    url = f"{base_url.rstrip('/')}/api/v1/correlate"
    payload = {
        "spill_id": spill_id,
        "time_window_hours": CORRELATE_WINDOW_HOURS,
    }
    return _request_json(
        "POST",
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )


def score_risk(base_url: str, spill_id: str) -> dict[str, Any]:
    url = f"{base_url.rstrip('/')}/api/v1/risk/score"
    payload = {"spill_id": spill_id}
    return _request_json(
        "POST",
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )


def _top_candidate(correlate: dict[str, Any]) -> dict[str, Any] | None:
    candidates = correlate.get("candidates") or []
    top_id = correlate.get("top_match_vessel_id")
    if top_id:
        for c in candidates:
            if c.get("vessel_id") == top_id:
                return c
    return candidates[0] if candidates else None


def _top_risk_vessel(risk: dict[str, Any]) -> dict[str, Any] | None:
    ranked = risk.get("ranked_vessels") or []
    primary = risk.get("primary_culprit_vessel_id")
    if primary:
        for v in ranked:
            if v.get("vessel_id") == primary:
                return v
    return ranked[0] if ranked else None


def print_section(title: str) -> None:
    print()
    print(title)
    print("-" * len(title))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="AquaTrace backend end-to-end smoke test (analyze → correlate → risk).",
    )
    parser.add_argument(
        "image",
        help="Path to SAR image (e.g. test_sar.png)",
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"API base URL (default: {DEFAULT_BASE_URL})",
    )
    args = parser.parse_args(argv)

    image_path = Path(args.image)
    if not image_path.is_file():
        _die(f"Image not found: {image_path.resolve()}")

    base_url = args.base_url.rstrip("/")

    # --- 1) Spill analyze ---
    print_section("1) POST /api/v1/spill/analyze")
    spill = analyze_spill(base_url, image_path)
    print(_pretty(spill))

    status = spill.get("status")
    spill_id = spill.get("spill_id")
    spill_detected = spill.get("spill_detected")
    confidence = spill.get("confidence")
    spill_area_pct = spill.get("spill_area_pct")
    inference_time_ms = spill.get("inference_time_ms")
    inference_mode = spill.get("inference_mode")

    print()
    print(f"status:             {status}")
    print(f"spill_id:           {spill_id}")
    print(f"spill_detected:     {spill_detected}")
    print(f"confidence:         {confidence}")
    print(f"spill_area_pct:     {spill_area_pct}")
    print(f"inference_time_ms:  {inference_time_ms}")
    print(f"inference_mode:     {inference_mode}")

    if not spill_id:
        _die("analyze response missing spill_id")

    # --- 2) Correlate ---
    print_section("2) POST /api/v1/correlate")
    corr = correlate_spill(base_url, spill_id)
    print(_pretty(corr))

    candidates = corr.get("candidates") or []
    matched_n = sum(1 for c in candidates if c.get("matched"))
    top = _top_candidate(corr)

    print()
    print(f"correlation status:     {corr.get('status')}")
    print(f"spill_source:           {corr.get('spill_source')}")
    print(f"matched vessels:        {matched_n}")
    print(f"top_match_vessel_id:    {corr.get('top_match_vessel_id')}")
    if top:
        print(f"top vessel name:        {top.get('vessel_name')}")
        print(f"spatial_overlap_score:  {top.get('spatial_overlap_score')}")
        print(f"temporal_overlap_score: {top.get('temporal_overlap_score')}")
        print(f"distance_to_spill_km:   {top.get('distance_to_spill_km')}")
        print(f"matched:                {top.get('matched')}")
    else:
        print("top vessel:              (none)")

    # --- 3) Risk ---
    print_section("3) POST /api/v1/risk/score")
    risk = score_risk(base_url, spill_id)
    print(_pretty(risk))

    top_risk = _top_risk_vessel(risk)
    print()
    print(f"risk status:               {risk.get('status')}")
    print(f"spill_source:              {risk.get('spill_source')}")
    print(f"primary_culprit_vessel_id: {risk.get('primary_culprit_vessel_id')}")
    if top_risk:
        print(f"top vessel name:           {top_risk.get('vessel_name')}")
        print(f"risk_score:                {top_risk.get('risk_score')}")
        print(f"risk_level:                {top_risk.get('risk_level')}")
        print(f"rationale:                 {top_risk.get('rationale')}")
    else:
        print("top vessel:                 (none)")

    # --- Summary ---
    no_spill = spill_detected is False
    if no_spill:
        top_name = "none"
        top_dist = "n/a"
        top_matched = False
        matched_n = 0
        primary = "none"
        risk_score = "n/a"
        risk_level = "n/a"
    else:
        top_name = (top or {}).get("vessel_name", "n/a")
        top_dist = (top or {}).get("distance_to_spill_km", "n/a")
        top_matched = (top or {}).get("matched", "n/a")
        risk_score = (top_risk or {}).get("risk_score", "n/a")
        risk_level = (top_risk or {}).get("risk_level", "n/a")
        primary = risk.get("primary_culprit_vessel_id") or "none"
        if primary is None:
            primary = "none"

    print()
    print("========================================")
    print("AQUATRACE END-TO-END TEST")
    print("========================================")
    print(f"SAR Detection: {spill_detected}")
    print(f"Confidence: {confidence}")
    print(f"Spill Area: {spill_area_pct}%")
    print(f"Inference: {inference_time_ms} ms")
    print(f"Spill ID: {spill_id}")
    if no_spill:
        print(
            "Outcome: no spill detected - correlation/risk correctly skipped"
        )
    print()
    print("CORRELATION")
    print(f"Source: {corr.get('spill_source')}")
    print(f"spill_detected: {corr.get('spill_detected')}")
    print(f"Matched Vessels: {matched_n}")
    print(f"Top Vessel: {top_name}")
    print(f"Distance: {top_dist} km")
    print(f"Match: {top_matched}")
    print()
    print("RISK")
    print(f"spill_detected: {risk.get('spill_detected')}")
    print(f"Primary Culprit: {primary}")
    print(f"Risk Score: {risk_score}")
    print(f"Risk Level: {risk_level}")
    print()
    print("========================================")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
