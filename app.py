import math
from typing import Any, Optional

import folium
import streamlit as st
from folium import plugins
from streamlit_folium import st_folium

import api_client
from api_client import BackendError

st.set_page_config(
    page_title="AquaSlick | Operations",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Maritime operations console — restrained, light workspace
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
}
.stApp {
    background: linear-gradient(180deg, #F4F6F8 0%, #E8EEF2 100%);
    color: #0F172A;
}
header[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbar"] { display: none; }

[data-testid="stSidebar"] {
    background: #FFFFFF;
    border-right: 1px solid #D0D7DE;
    box-shadow: none;
}
[data-testid="stSidebar"] > div:first-child { padding-top: 0.75rem; }

.block-container {
    padding: 0.75rem 1rem 1rem 1rem !important;
    max-width: 100% !important;
}

.ops-brand {
    font-size: 1.35rem;
    font-weight: 700;
    color: #0B3A5C;
    letter-spacing: -0.02em;
    margin: 0;
}
.ops-subtitle {
    font-size: 0.8rem;
    color: #64748B;
    margin: 0.15rem 0 0.85rem 0;
}
.ops-chip {
    display: inline-block;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 0.2rem 0.55rem;
    border-radius: 4px;
    border: 1px solid #D0D7DE;
    background: #F8FAFC;
    color: #334155;
    margin-bottom: 0.75rem;
}
.ops-chip.ok { border-color: #A7F3D0; background: #ECFDF5; color: #065F46; }
.ops-chip.err { border-color: #FECACA; background: #FEF2F2; color: #991B1B; }

.ops-section {
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: #64748B;
    margin: 1rem 0 0.45rem 0;
}
.ops-card {
    background: #FFFFFF;
    border: 1px solid #D0D7DE;
    border-radius: 8px;
    padding: 0.9rem 1rem;
    margin-bottom: 0.75rem;
}
.ops-card.alert {
    border-left: 3px solid #B42318;
}
.ops-name {
    font-size: 1.1rem;
    font-weight: 600;
    color: #0F172A;
    margin: 0 0 0.65rem 0;
}
.ops-row {
    display: flex;
    justify-content: space-between;
    gap: 0.75rem;
    font-size: 0.85rem;
    padding: 0.35rem 0;
    border-bottom: 1px solid #EEF2F6;
}
.ops-row:last-child { border-bottom: none; }
.ops-label { color: #64748B; }
.ops-value { color: #0F172A; font-weight: 500; text-align: right; }
.ops-mono { font-family: "IBM Plex Mono", ui-monospace, monospace; font-size: 0.82rem; }

.ops-metric {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 0.7rem 0.75rem;
    text-align: left;
}
.ops-metric .k {
    font-size: 0.68rem;
    font-weight: 600;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}
.ops-metric .v {
    font-size: 1.15rem;
    font-weight: 600;
    color: #0B3A5C;
    margin-top: 0.2rem;
}
.ops-metric .v.critical { color: #B42318; }
.ops-metric .v.high { color: #B45309; }
.ops-metric .v.moderate { color: #A16207; }
.ops-metric .v.low { color: #047857; }

.ops-note {
    font-size: 0.82rem;
    color: #334155;
    line-height: 1.45;
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 0.75rem 0.85rem;
}
.ops-idle {
    padding: 1.25rem 0.5rem;
    text-align: left;
}
.ops-idle h4 {
    margin: 0 0 0.35rem 0;
    color: #0F172A;
    font-weight: 600;
    font-size: 1rem;
}
.ops-idle p {
    margin: 0;
    color: #64748B;
    font-size: 0.85rem;
    line-height: 1.45;
}
.ops-banner {
    background: #FEF2F2;
    border: 1px solid #FECACA;
    border-radius: 8px;
    padding: 0.75rem 0.85rem;
    margin-bottom: 0.75rem;
    font-size: 0.82rem;
    color: #991B1B;
}
.ops-banner strong { display: block; margin-bottom: 0.25rem; }

div[data-testid="stSidebar"] button {
    border-radius: 6px !important;
    font-weight: 500 !important;
}
</style>
""",
    unsafe_allow_html=True,
)

if "selected_vessel_id" not in st.session_state:
    st.session_state.selected_vessel_id = None


def _load_map_vessels() -> tuple[list[dict], dict]:
    """Fetch vessels + trajectories + spill footprint from the API."""
    summaries = api_client.get_vessels()
    spill = api_client.analyze_spill()

    spill_poly = [[p["lat"], p["lon"]] for p in spill.get("footprint", {}).get("polygon", [])]
    area_label = f"{spill.get('footprint', {}).get('area_sq_km', 0)} sq km"

    loaded: list[dict] = []
    for s in summaries:
        vid = s["vessel_id"]
        traj = api_client.get_trajectory(vid)
        path = [[p["lat"], p["lon"]] for p in traj.get("points", [])]
        loaded.append(
            {
                "id": vid,
                "name": s["name"],
                "mmsi": s["mmsi"],
                "type": s["vessel_type"],
                "speed": f"{s['speed_kts']} kts",
                "marker_loc": [s["lat"], s["lon"]],
                "path": path,
                "spill": spill_poly,
                "area": area_label,
            }
        )
    return loaded, spill


def _risk_class(level: str) -> str:
    level = (level or "").lower()
    if level in {"critical", "high", "moderate", "low"}:
        return level
    return ""


backend_error: Optional[str] = None
vessels: list[dict] = []

try:
    vessels, _spill = _load_map_vessels()
except BackendError as exc:
    backend_error = exc.message
    vessels = []
    if st.session_state.selected_vessel_id is not None:
        st.session_state.selected_vessel_id = None

active_vessel = next((v for v in vessels if v["id"] == st.session_state.selected_vessel_id), None)
selection_error: Optional[str] = None
correlation_line = "Select a vessel to run spill–AIS correlation."
confidence_label = "—"
risk_level = ""
risk_factors: list[dict[str, Any]] = []
spatial_score = None
temporal_score = None
distance_km = None
matched = False

if active_vessel and backend_error is None:
    try:
        detail = api_client.get_vessel(active_vessel["id"])
        active_vessel["name"] = detail.get("name", active_vessel["name"])
        active_vessel["mmsi"] = detail.get("mmsi", active_vessel["mmsi"])
        active_vessel["type"] = detail.get("vessel_type", active_vessel["type"])
        active_vessel["speed"] = f"{detail.get('speed_kts', 0)} kts"
        active_vessel["marker_loc"] = [
            detail.get("lat", active_vessel["marker_loc"][0]),
            detail.get("lon", active_vessel["marker_loc"][1]),
        ]

        traj = api_client.get_trajectory(active_vessel["id"])
        active_vessel["path"] = [[p["lat"], p["lon"]] for p in traj.get("points", [])]

        corr = api_client.correlate_vessel(active_vessel["id"])
        candidate = next(
            (c for c in corr.get("candidates", []) if c.get("vessel_id") == active_vessel["id"]),
            None,
        )
        if candidate:
            spatial_score = candidate.get("spatial_overlap_score")
            temporal_score = candidate.get("temporal_overlap_score")
            distance_km = candidate.get("distance_to_spill_km")
            matched = bool(candidate.get("matched"))
            if matched:
                correlation_line = (
                    f"Spatial–temporal match. "
                    f"Distance {distance_km} km · "
                    f"spatial {float(spatial_score or 0):.2f} · "
                    f"temporal {float(temporal_score or 0):.2f}."
                )
            else:
                correlation_line = candidate.get("notes") or "No strong spatial–temporal match."
        else:
            correlation_line = corr.get("message", "Correlation complete.")

        risk = api_client.score_risk(active_vessel["id"])
        ranked = risk.get("ranked_vessels", [])
        vessel_risk = next(
            (r for r in ranked if r.get("vessel_id") == active_vessel["id"]),
            ranked[0] if ranked else None,
        )
        if vessel_risk:
            score_pct = float(vessel_risk.get("risk_score", 0.0)) * 100.0
            confidence_label = f"{score_pct:.1f}%"
            risk_level = str(vessel_risk.get("risk_level", "")).upper()
            active_vessel["confidence"] = confidence_label
            active_vessel["risk_rationale"] = vessel_risk.get("rationale", "")
            risk_factors = vessel_risk.get("factors") or []
        else:
            active_vessel["confidence"] = "—"
    except BackendError as exc:
        selection_error = exc.message
        active_vessel["confidence"] = "—"

# --- Operations panel (sidebar) ---
with st.sidebar:
    st.markdown('<p class="ops-brand">AquaSlick</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="ops-subtitle">Oil spill &amp; AIS correlation</p>',
        unsafe_allow_html=True,
    )

    if backend_error:
        st.markdown(
            f'<div class="ops-chip err">API offline</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="ops-banner"><strong>Cannot reach backend</strong>{backend_error}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="ops-chip ok">API connected · {len(vessels)} vessels</div>',
            unsafe_allow_html=True,
        )

    if selection_error:
        st.markdown(
            f'<div class="ops-banner"><strong>Selection sync failed</strong>{selection_error}</div>',
            unsafe_allow_html=True,
        )

    if active_vessel:
        st.markdown('<div class="ops-section">Incident case</div>', unsafe_allow_html=True)
        status_label = "Matched to spill" if matched else "Under review"
        st.markdown(
            f"""
            <div class="ops-card alert">
              <p class="ops-name">{active_vessel['name']}</p>
              <div class="ops-row"><span class="ops-label">Status</span><span class="ops-value">{status_label}</span></div>
              <div class="ops-row"><span class="ops-label">MMSI</span><span class="ops-value ops-mono">{active_vessel['mmsi']}</span></div>
              <div class="ops-row"><span class="ops-label">Vessel class</span><span class="ops-value">{active_vessel['type']}</span></div>
              <div class="ops-row"><span class="ops-label">Speed</span><span class="ops-value">{active_vessel['speed']}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        conf_value = active_vessel.get("confidence", confidence_label)
        risk_css = _risk_class(risk_level)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(
                f"""
                <div class="ops-metric">
                  <div class="k">Risk score</div>
                  <div class="v {risk_css}">{conf_value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f"""
                <div class="ops-metric">
                  <div class="k">Spill area</div>
                  <div class="v">{active_vessel.get('area', '—')}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if risk_level:
            st.caption(f"Risk level: **{risk_level.title()}**")

        st.markdown('<div class="ops-section">Correlation</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="ops-note">{correlation_line}</div>', unsafe_allow_html=True)

        if risk_factors:
            st.markdown('<div class="ops-section">Risk factors</div>', unsafe_allow_html=True)
            factor_rows = ""
            for f in risk_factors:
                name = str(f.get("name", "")).replace("_", " ").title()
                weight = float(f.get("weight", 0))
                score = float(f.get("score", 0))
                detail = f.get("detail", "")
                factor_rows += (
                    f'<div class="ops-row"><span class="ops-label">{name} '
                    f'(w={weight:.2f})</span>'
                    f'<span class="ops-value">{score:.2f}</span></div>'
                    f'<div style="font-size:0.75rem;color:#64748B;margin:0 0 0.45rem 0;">{detail}</div>'
                )
            st.markdown(
                f'<div class="ops-card">{factor_rows}</div>',
                unsafe_allow_html=True,
            )

        rationale = active_vessel.get("risk_rationale")
        if rationale:
            st.caption(rationale)

        dossier = (
            f"AquaSlick Incident Report\n"
            f"Vessel: {active_vessel['name']}\n"
            f"MMSI: {active_vessel['mmsi']}\n"
            f"Risk score: {active_vessel.get('confidence', '—')}\n"
            f"Risk level: {risk_level or '—'}\n"
            f"Coordinates: {active_vessel['marker_loc']}\n"
            f"Rationale: {active_vessel.get('risk_rationale', 'n/a')}\n"
        )
        st.download_button(
            "Export incident report",
            data=dossier,
            file_name=f"aquaslick_incident_{active_vessel['id']}.txt",
            type="primary",
            use_container_width=True,
        )

        if st.button("Clear selection", use_container_width=True):
            st.session_state.selected_vessel_id = None
            st.rerun()

    else:
        st.markdown('<div class="ops-section">Fleet</div>', unsafe_allow_html=True)
        if vessels and not backend_error:
            for v in vessels:
                st.markdown(
                    f"""
                    <div class="ops-card" style="padding:0.65rem 0.75rem;margin-bottom:0.45rem;">
                      <div style="font-weight:600;color:#0F172A;font-size:0.9rem;">{v['name']}</div>
                      <div style="font-size:0.75rem;color:#64748B;margin-top:0.2rem;">
                        <span class="ops-mono">{v['mmsi']}</span> · {v['type']} · {v['speed']}
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            idle_msg = "Select a vessel marker on the map to open the incident case."
        elif backend_error:
            idle_msg = "Backend offline — map telemetry unavailable."
        else:
            idle_msg = "No vessels returned from the API."

        st.markdown(
            f"""
            <div class="ops-idle">
              <h4>Operations map</h4>
              <p>{idle_msg}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

# --- Map (visual hero) ---
# Initial: all markers + all tracks (dotted). Spill only when a vessel is selected.
SPILL_COLOR = "#C45C4A"
TRACK_SELECTED = "#1D4E89"
TRACK_IDLE = "#7B8FA6"

if "map_center" not in st.session_state:
    st.session_state.map_center = [18.50, 84.50]
if "map_zoom" not in st.session_state:
    st.session_state.map_zoom = 7

m = folium.Map(
    location=st.session_state.map_center,
    zoom_start=st.session_state.map_zoom,
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr="Esri",
)

selected_id = st.session_state.selected_vessel_id

# 1) Trajectories: full path for every vessel (selected solid, others dotted/faint)
for v in vessels:
    path = v.get("path") or []
    if not path:
        continue
    is_selected = v["id"] == selected_id
    if is_selected:
        folium.PolyLine(
            locations=path,
            color=TRACK_SELECTED,
            weight=5,
            opacity=0.95,
            tooltip=f"{v['name']} track",
        ).add_to(m)
    else:
        folium.PolyLine(
            locations=path,
            color=TRACK_IDLE,
            weight=2,
            opacity=0.40,
            dash_array="4, 10",
            tooltip=f"{v['name']} track",
        ).add_to(m)

# 2) Spill polygon: only for the selected vessel (hidden in initial state)
if selected_id:
    selected_vessel = next((v for v in vessels if v["id"] == selected_id), None)
    if selected_vessel and selected_vessel.get("spill"):
        folium.Polygon(
            locations=selected_vessel["spill"],
            color=SPILL_COLOR,
            fill=True,
            fill_color=SPILL_COLOR,
            fill_opacity=0.50,
            weight=2.5,
            tooltip="Detected spill footprint",
        ).add_to(m)

# 3) Markers: always show all vessels; selected state is distinct
for v in vessels:
    is_selected = v["id"] == selected_id
    folium.Marker(
        location=v["marker_loc"],
        tooltip=v["name"],
        icon=folium.Icon(
            color="darkblue" if is_selected else "cadetblue",
            icon="ship",
            prefix="fa",
        ),
    ).add_to(m)

map_data = st_folium(
    m,
    key="aquaslick_ops_map",
    use_container_width=True,
    height=820,
    returned_objects=["last_object_clicked", "center", "zoom"],
)

# Preserve viewport across selection reruns
if map_data:
    center = map_data.get("center")
    zoom = map_data.get("zoom")
    if isinstance(center, dict) and "lat" in center and ("lng" in center or "lon" in center):
        st.session_state.map_center = [
            center["lat"],
            center.get("lng", center.get("lon")),
        ]
    if zoom is not None:
        st.session_state.map_zoom = zoom

if map_data and map_data.get("last_object_clicked") and vessels:
    clicked_lat = map_data["last_object_clicked"]["lat"]
    clicked_lng = map_data["last_object_clicked"]["lng"]

    for v in vessels:
        dist = math.hypot(v["marker_loc"][0] - clicked_lat, v["marker_loc"][1] - clicked_lng)
        if dist < 0.1:
            if st.session_state.selected_vessel_id != v["id"]:
                st.session_state.selected_vessel_id = v["id"]
                st.rerun()
