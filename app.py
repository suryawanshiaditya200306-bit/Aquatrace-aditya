import math
from typing import Any, Optional

import folium
import streamlit as st
from streamlit_folium import st_folium

import api_client
from api_client import BackendError

st.set_page_config(
    page_title="AquaSlick | Ocean Environmental Command",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.stApp {
    background: radial-gradient(circle at 50% 15%, #101F38 0%, #08101E 100%);
    color: #F8FAFC !important;
}
header[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbar"] { display: none; }

iframe {
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 12px !important;
    outline: none !important;
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.35);
}
div[data-testid="stCustomComponentV1"] {
    border: none !important;
    background: transparent !important;
    padding: 0 !important;
}

[data-testid="stSidebar"] {
    background-color: #0B1526 !important;
    border-right: 1px solid rgba(255, 255, 255, 0.07) !important;
    width: 24rem !important;
    min-width: 24rem !important;
}
[data-testid="stSidebar"] > div:first-child { padding-top: 1rem; }

.block-container {
    max-width: 1200px !important;
    margin: 0 auto !important;
    padding: 2rem 1.5rem 3rem 1.5rem !important;
}

/* Home / Landing Styles */
.hero-wrapper {
    max-width: 760px;
    margin: 2rem auto 2.5rem auto;
    text-align: center;
}
.hero-pill {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    color: #38BDF8;
    background: rgba(56, 189, 248, 0.1);
    border: 1px solid rgba(56, 189, 248, 0.25);
    padding: 0.35rem 1rem;
    border-radius: 9999px;
    display: inline-block;
    margin-bottom: 1.25rem;
}
.hero-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 4.4rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: #FFFFFF;
    line-height: 1.05;
    margin-bottom: 1rem;
    text-shadow: 0 4px 24px rgba(56, 189, 248, 0.2);
}
.hero-desc {
    font-size: 1.05rem;
    color: #94A3B8;
    line-height: 1.6;
    margin-bottom: 1.5rem;
    max-width: 36rem;
    margin-left: auto;
    margin-right: auto;
}

.section-meta {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.85rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: #38BDF8;
    margin-bottom: 1rem;
    text-align: center;
}
.target-card {
    background: rgba(16, 28, 50, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(8px);
    border-radius: 12px;
    padding: 1.1rem 1rem;
    min-height: 120px;
    transition: all 0.2s ease;
}
.target-card:hover {
    border-color: rgba(56, 189, 248, 0.4);
    transform: translateY(-2px);
}
.target-card.selected {
    border-color: #EF4444 !important;
    background: rgba(239, 68, 68, 0.08) !important;
    box-shadow: 0 8px 24px rgba(239, 68, 68, 0.15);
}
.target-card .v-title {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 1.05rem;
    color: #F8FAFC;
    margin-bottom: 0.35rem;
}
.target-card .v-info {
    font-size: 0.82rem;
    color: #94A3B8;
    line-height: 1.5;
}

.upload-deck {
    background: rgba(14, 25, 45, 0.5);
    border: 1px dashed rgba(56, 189, 248, 0.25);
    border-radius: 14px;
    padding: 1.5rem;
    margin: 2.5rem auto 1.5rem auto;
    max-width: 620px;
    text-align: center;
}
.upload-deck-title {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    font-size: 1.05rem;
    color: #F8FAFC;
    margin-bottom: 0.25rem;
}
.upload-deck-sub {
    font-size: 0.82rem;
    color: #64748B;
    margin-bottom: 1rem;
}

.brand-head {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.7rem;
    font-weight: 700;
    color: #FFFFFF;
    margin: 0;
}
.status-pill {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    padding: 0.2rem 0.55rem;
    border-radius: 6px;
    margin: 0.4rem 0 1rem 0;
}
.status-pill.ok { border: 1px solid rgba(16, 185, 129, 0.3); background: rgba(16, 185, 129, 0.15); color: #34D399; }
.status-pill.err { border: 1px solid rgba(239, 68, 68, 0.3); background: rgba(239, 68, 68, 0.15); color: #FCA5A5; }

.section-tag {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: #38BDF8;
    margin: 1.1rem 0 0.45rem 0;
    padding-bottom: 0.3rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.metric-panel {
    background: rgba(16, 28, 50, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 0.85rem 0.95rem;
    margin-bottom: 0.65rem;
}
.metric-panel.alert { border-left: 3px solid #EF4444; }
.metric-panel.clear { border-left: 3px solid #10B981; }

.panel-row {
    display: flex;
    justify-content: space-between;
    padding: 0.32rem 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    font-size: 0.82rem;
}
.panel-row:last-child { border-bottom: none; }
.panel-lbl { color: #8292A6; }
.panel-val { color: #F1F5F9; font-weight: 500; font-family: 'JetBrains Mono', monospace; }

.level-tag {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.68rem;
    padding: 0.15rem 0.45rem;
    border-radius: 4px;
    font-weight: 600;
}
.level-tag.critical { background: rgba(239, 68, 68, 0.2); color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.3); }
.level-tag.nominal { background: rgba(16, 185, 129, 0.2); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.3); }
</style>
""",
    unsafe_allow_html=True,
)

# STRICTLY NON-RED, NON-ORANGE BASE PALETTE FOR FLEET MARKERS
FLEET_PALETTE = [
    {"folium_color": "blue", "hex": "#38BDF8"},       # Cyan / Light Blue
    {"folium_color": "purple", "hex": "#A855F7"},     # Purple
    {"folium_color": "darkblue", "hex": "#1D4ED8"},   # Deep Blue
    {"folium_color": "green", "hex": "#10B981"},      # Emerald
    {"folium_color": "cadetblue", "hex": "#0D9488"},  # Teal / Cadet
    {"folium_color": "gray", "hex": "#64748B"},       # Slate Gray
]

if "view_state" not in st.session_state:
    st.session_state.view_state = "home"
if "selected_vessel_id" not in st.session_state:
    st.session_state.selected_vessel_id = None
if "compare_vessel_id" not in st.session_state:
    st.session_state.compare_vessel_id = None
if "spill_id" not in st.session_state:
    st.session_state.spill_id = None
if "spill_analysis" not in st.session_state:
    st.session_state.spill_analysis = None
if "last_click" not in st.session_state:
    st.session_state.last_click = None


def _load_map_vessels() -> tuple[list[dict], dict]:
    summaries = api_client.get_vessels()
    spill = st.session_state.spill_analysis
    if not isinstance(spill, dict):
        spill = api_client.analyze_spill()

    spill_poly = [[p["lat"], p["lon"]] for p in spill.get("footprint", {}).get("polygon", [])]
    area_label = f"{spill.get('footprint', {}).get('area_sq_km', 0)} sq km"

    loaded: list[dict] = []
    for idx, s in enumerate(summaries):
        vid = s["vessel_id"]
        try:
            traj = api_client.get_trajectory(vid)
            path = [[p["lat"], p["lon"]] for p in traj.get("points", [])]
        except Exception:
            path = []
        color_entry = FLEET_PALETTE[idx % len(FLEET_PALETTE)]
        loaded.append(
            {
                "id": vid,
                "name": s["name"],
                "mmsi": s["mmsi"],
                "type": s["vessel_type"],
                "speed": f"{s.get('speed_kts', 0)} kts",
                "marker_loc": [s["lat"], s["lon"]],
                "path": path,
                "spill": spill_poly,
                "area": area_label,
                "folium_color": color_entry["folium_color"],
                "theme_hex": color_entry["hex"],
            }
        )
    return loaded, spill


backend_error: Optional[str] = None
vessels: list[dict] = []
spill: dict[str, Any] = {}

try:
    vessels, spill = _load_map_vessels()
except BackendError as exc:
    backend_error = exc.message
except Exception as e:
    backend_error = str(e)


# ==============================================================================
# VIEW 1: HOME LANDING SCREEN
# ==============================================================================
if st.session_state.view_state == "home":
    st.markdown(
        """
        <div class="hero-wrapper">
            <span class="hero-pill">Coastal Defense &amp; Satellite Analytics</span>
            <div class="hero-title">AquaSlick</div>
            <div class="hero-desc">
                Real-time Sentinel-1 SAR oil slick segmentation and automated AIS trajectory attribution.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-meta">Tracked Vessels in Sector</div>', unsafe_allow_html=True)
    top_4_vessels = vessels[:4] if len(vessels) >= 4 else vessels
    if top_4_vessels:
        cols = st.columns(len(top_4_vessels))
        for idx, v in enumerate(top_4_vessels):
            with cols[idx]:
                is_selected = st.session_state.selected_vessel_id == v["id"]
                card_class = "selected" if is_selected else ""

                st.markdown(
                    f"""
                    <div class="target-card {card_class}">
                        <div class="v-title">{v['name']}</div>
                        <div class="v-info">{v['type']}</div>
                        <div class="v-info">MMSI: {v['mmsi']}</div>
                        <div class="v-info" style="color:{'#EF4444' if is_selected else v['theme_hex']}; font-weight:600;">{v['speed']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                btn_txt = "Deselect" if is_selected else "Select Vessel"
                if st.button(btn_txt, key=f"sel_btn_{v['id']}", use_container_width=True):
                    st.session_state.selected_vessel_id = None if is_selected else v["id"]
                    st.rerun()

    st.markdown(
        """
        <div class="upload-deck">
            <div class="upload-deck-title">Ingest SAR Satellite Capture</div>
            <div class="upload-deck-sub">Upload Sentinel-1 SAR imagery (.png, .jpg, .jpeg) for automated detection</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c_u1, c_u2, c_u3 = st.columns([1, 1.8, 1])
    with c_u2:
        home_sar = st.file_uploader(
            "SAR Frame Upload",
            type=["png", "jpg", "jpeg"],
            key="home_sar_upload",
            label_visibility="collapsed",
        )
        if home_sar and st.button("Process Scene & Seed Incident", use_container_width=True):
            try:
                with st.spinner("Analyzing radar reflections…"):
                    res = api_client.analyze_spill(
                        home_sar,
                        filename=getattr(home_sar, "name", "sar_image.png"),
                        content_type=getattr(home_sar, "type", None),
                    )
                    st.session_state.spill_analysis = res
                    st.session_state.spill_id = res.get("spill_id")
                    st.success("Incident registered in PostGIS database.")
            except BackendError as exc:
                st.error(exc.message)

    c_b1, c_b2, c_b3 = st.columns([1.2, 1.5, 1.2])
    with c_b2:
        st.write("")
        if st.button("LAUNCH OPERATIONS MAP", type="primary", use_container_width=True):
            st.session_state.view_state = "ops"
            st.rerun()

        st.markdown(
            f"""
            <div style="margin-top: 1rem; text-align: center; font-size: 0.8rem; font-family: 'JetBrains Mono', monospace; color: #64748B;">
                System Status: <span style="color: {'#EF4444' if backend_error else '#34D399'};">
                    {'API OFFLINE' if backend_error else f'CONNECTED ({len(vessels)} Tracks Live)'}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.stop()


# ==============================================================================
# VIEW 2: OPERATIONS DASHBOARD
# ==============================================================================
spill_polygon = [[p["lat"], p["lon"]] for p in spill.get("footprint", {}).get("polygon", [])]
centroid = None
if spill_polygon:
    c_lat = sum(p[0] for p in spill_polygon) / len(spill_polygon)
    c_lon = sum(p[1] for p in spill_polygon) / len(spill_polygon)
    centroid = [c_lat, c_lon]


def _calc_dist(loc):
    if not centroid or not loc:
        return 0.0
    return math.hypot(loc[0] - centroid[0], loc[1] - centroid[1]) * 111.0


def _fetch_profile(vid: str):
    if not vid:
        return None
    raw_v = next((v for v in vessels if v["id"] == vid), None)
    if not raw_v:
        return None

    bundle = {
        "id": vid,
        "name": raw_v["name"],
        "mmsi": raw_v["mmsi"],
        "type": raw_v["type"],
        "speed": raw_v["speed"],
        "loc": raw_v["marker_loc"],
        "dist_km": round(_calc_dist(raw_v["marker_loc"]), 2),
        "risk_pct": "0.0%",
        "risk_level": "NOMINAL",
        "matched": False,
        "theme_hex": raw_v.get("theme_hex", "#38BDF8"),
        "rationale": "Operating on regular maritime corridor. No spill correlation detected.",
    }

    try:
        corr = api_client.correlate_vessel(vid, spill_id=st.session_state.spill_id)
        candidate = next((c for c in corr.get("candidates", []) if c.get("vessel_id") == vid), None)
        risk = api_client.score_risk(vid, spill_id=st.session_state.spill_id)
        ranked = risk.get("ranked_vessels", [])
        v_risk = next((r for r in ranked if r.get("vessel_id") == vid), (ranked[0] if ranked else None))

        if candidate:
            bundle["dist_km"] = candidate.get("distance_to_spill_km", bundle["dist_km"])
            bundle["matched"] = bool(candidate.get("matched"))

        if v_risk:
            score_val = float(v_risk.get("risk_score", 0.0)) * 100.0
            bundle["risk_pct"] = f"{score_val:.1f}%"
            bundle["risk_level"] = str(v_risk.get("risk_level", "NOMINAL")).upper()
            bundle["rationale"] = v_risk.get("rationale", bundle["rationale"])
    except Exception:
        pass

    return bundle


primary_profile = _fetch_profile(st.session_state.selected_vessel_id)
compare_profile = _fetch_profile(st.session_state.compare_vessel_id)

# --- SIDEBAR TELEMETRY ---
with st.sidebar:
    st.markdown('<p class="brand-head">AquaSlick</p>', unsafe_allow_html=True)
    if backend_error:
        st.markdown('<span class="status-pill err">API Offline</span>', unsafe_allow_html=True)
    else:
        st.markdown(f'<span class="status-pill ok">Connected · {len(vessels)} Tracks Live</span>', unsafe_allow_html=True)

    # 1. Target Vessel Information
    st.markdown('<div class="section-tag">1. Target Telemetry</div>', unsafe_allow_html=True)
    v_dict = {v["id"]: f"{v['name']} ({v['mmsi']})" for v in vessels}

    if primary_profile:
        is_culprit = primary_profile["matched"] or primary_profile["risk_level"] in ["HIGH", "CRITICAL"]
        card_class = "alert" if is_culprit else "clear"
        badge_class = "critical" if is_culprit else "nominal"

        st.markdown(
            f"""
            <div class="metric-panel {card_class}">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.4rem;">
                <span style="font-weight:700;font-size:0.95rem;color:#F8FAFC;">{primary_profile['name']}</span>
                <span class="level-tag {badge_class}">{primary_profile['risk_level']}</span>
              </div>
              <div class="panel-row"><span class="panel-lbl">MMSI</span><span class="panel-val">{primary_profile['mmsi']}</span></div>
              <div class="panel-row"><span class="panel-lbl">Class</span><span class="panel-val">{primary_profile['type']}</span></div>
              <div class="panel-row"><span class="panel-lbl">Speed</span><span class="panel-val">{primary_profile['speed']}</span></div>
              <div class="panel-row"><span class="panel-lbl">Distance to Slick</span><span class="panel-val">{primary_profile['dist_km']} km</span></div>
              <div class="panel-row"><span class="panel-lbl">Risk Attribution</span><span class="panel-val" style="color:#EF4444;">{primary_profile['risk_pct']}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(primary_profile["rationale"])

        if st.button("Deselect Target", use_container_width=True):
            st.session_state.selected_vessel_id = None
            st.rerun()
    else:
        st.info("Select any vessel marker on the map to inspect telemetry.")
        if v_dict:
            sel_target = st.selectbox(
                "Manual Selection",
                options=[None] + list(v_dict.keys()),
                format_func=lambda x: "Choose from fleet..." if x is None else v_dict.get(x, x),
                index=0,
                key="manual_v_select",
            )
            if sel_target:
                st.session_state.selected_vessel_id = sel_target
                st.rerun()

    # 2. SAR Analysis
    st.markdown('<div class="section-tag">2. SAR Detection</div>', unsafe_allow_html=True)
    ops_sar = st.file_uploader(
        "Upload SAR scene",
        type=["png", "jpg", "jpeg"],
        key="ops_sar_file",
        label_visibility="collapsed",
    )
    if st.button("Analyze Scene", use_container_width=True, disabled=ops_sar is None):
        try:
            with st.spinner("Processing segmentation…"):
                res = api_client.analyze_spill(
                    ops_sar,
                    filename=getattr(ops_sar, "name", "sar_image.png"),
                    content_type=getattr(ops_sar, "type", None),
                )
                st.session_state.spill_analysis = res
                st.session_state.spill_id = res.get("spill_id")
                st.rerun()
        except BackendError as exc:
            st.error(exc.message)

    spill_res = st.session_state.spill_analysis
    if isinstance(spill_res, dict):
        st.markdown(
            f"""
            <div class="metric-panel">
              <div class="panel-row"><span class="panel-lbl">Slick Area</span><span class="panel-val">{spill_res.get('footprint', {}).get('area_sq_km', 0)} km²</span></div>
              <div class="panel-row"><span class="panel-lbl">SAR Confidence</span><span class="panel-val">{float(spill_res.get('confidence', 0.94))*100:.1f}%</span></div>
              <div class="panel-row"><span class="panel-lbl">Inference Latency</span><span class="panel-val">{spill_res.get('inference_time_ms', 42)} ms</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 3. Dual Vessel Comparison
    st.markdown('<div class="section-tag">3. Dual Vessel Comparison</div>', unsafe_allow_html=True)
    comp_choices = [None] + [v for v in v_dict.keys() if v != st.session_state.selected_vessel_id]
    idx_c = comp_choices.index(st.session_state.compare_vessel_id) if st.session_state.compare_vessel_id in comp_choices else 0

    sel_comp = st.selectbox(
        "Compare Against",
        options=comp_choices,
        format_func=lambda x: "None (Single Target)" if x is None else v_dict.get(x, x),
        index=idx_c,
        key="sb_compare",
        label_visibility="collapsed",
    )
    if sel_comp != st.session_state.compare_vessel_id:
        st.session_state.compare_vessel_id = sel_comp
        st.rerun()

    if primary_profile and compare_profile:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(
                f"""
                <div class="metric-panel alert" style="padding:0.55rem;">
                  <div style="font-weight:700;font-size:0.75rem;color:#FFFFFF;">{primary_profile['name']}</div>
                  <div class="panel-row"><span class="panel-lbl">Risk</span><span class="panel-val">{primary_profile['risk_pct']}</span></div>
                  <div class="panel-row"><span class="panel-lbl">Dist</span><span class="panel-val">{primary_profile['dist_km']}km</span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f"""
                <div class="metric-panel" style="padding:0.55rem; border-left: 3px solid #F59E0B;">
                  <div style="font-weight:700;font-size:0.75rem;color:#FFFFFF;">{compare_profile['name']}</div>
                  <div class="panel-row"><span class="panel-lbl">Risk</span><span class="panel-val">{compare_profile['risk_pct']}</span></div>
                  <div class="panel-row"><span class="panel-lbl">Dist</span><span class="panel-val">{compare_profile['dist_km']}km</span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # 4. Dossier Actions
    st.markdown('<div class="section-tag">4. Incident Dossier</div>', unsafe_allow_html=True)
    if primary_profile:
        report = (
            f"AquaSlick Incident Report\n"
            f"========================\n"
            f"Target Vessel: {primary_profile['name']} (MMSI: {primary_profile['mmsi']})\n"
            f"Classification: {primary_profile['type']}\n"
            f"Distance to Slick: {primary_profile['dist_km']} km\n"
            f"Risk Confidence: {primary_profile['risk_pct']} ({primary_profile['risk_level']})\n"
            f"Notes: {primary_profile['rationale']}\n"
        )
        st.download_button(
            "Export Incident Dossier",
            data=report,
            file_name=f"aquaslick_dossier_{primary_profile['id']}.txt",
            type="primary",
            use_container_width=True,
        )

    if st.button("Return to Mission Home", use_container_width=True):
        st.session_state.view_state = "home"
        st.rerun()


# --- OPERATIONS MAP CANVAS ---
default_loc = centroid if centroid else [18.50, 84.50]

m = folium.Map(
    location=default_loc,
    zoom_start=8,
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr="Esri World Imagery",
)

# 1. Spill Footprint (Red Polygon)
if spill_polygon:
    folium.Polygon(
        locations=spill_polygon,
        color="#EF4444",
        fill=True,
        fill_color="#DC2626",
        fill_opacity=0.70,
        weight=3,
        tooltip=f"Detected Oil Slick: {spill.get('footprint', {}).get('area_sq_km', 0)} km²",
    ).add_to(m)

# 2. Vessel Trajectories (Only Selected turns RED; Secondary turns ORANGE; all others stay cool/neutral)
for v in vessels:
    path = v.get("path") or []
    if not path:
        continue
    is_p = v["id"] == st.session_state.selected_vessel_id
    is_c = v["id"] == st.session_state.compare_vessel_id

    dist_km = _calc_dist(v["marker_loc"])
    line_color = "#EF4444" if is_p else ("#F59E0B" if is_c else v["theme_hex"])
    weight = 4.5 if (is_p or is_c) else 2.2
    opacity = 0.95 if (is_p or is_c) else 0.60
    dash = None if (is_p or is_c) else "3, 6"

    folium.PolyLine(
        locations=path,
        color=line_color,
        weight=weight,
        opacity=opacity,
        dash_array=dash,
        tooltip=f"{v['name']} ({v['type']}) — Distance: {dist_km:.1f} km from slick",
    ).add_to(m)

# 3. Direct Distance Vectors from Centroid (Visible only for selected target/secondary)
if centroid:
    if primary_profile:
        folium.PolyLine(
            locations=[centroid, primary_profile["loc"]],
            color="#EF4444",
            weight=2,
            dash_array="5, 6",
            tooltip=f"Vector to {primary_profile['name']}: {primary_profile['dist_km']} km",
        ).add_to(m)
    if compare_profile:
        folium.PolyLine(
            locations=[centroid, compare_profile["loc"]],
            color="#F59E0B",
            weight=2,
            dash_array="5, 6",
            tooltip=f"Vector to {compare_profile['name']}: {compare_profile['dist_km']} km",
        ).add_to(m)

# 4. Markers (Only Selected turns RED; Secondary turns ORANGE; All others are non-red)
for v in vessels:
    is_p = v["id"] == st.session_state.selected_vessel_id
    is_c = v["id"] == st.session_state.compare_vessel_id

    marker_color = "red" if is_p else ("orange" if is_c else v["folium_color"])
    dist_km = _calc_dist(v["marker_loc"])

    folium.Marker(
        location=v["marker_loc"],
        tooltip=f"{v['name']} ({v['type']}) — {dist_km:.1f} km to slick",
        icon=folium.Icon(color=marker_color, icon="ship", prefix="fa"),
    ).add_to(m)

map_data = st_folium(
    m,
    key="aquaslick_map_view",
    use_container_width=True,
    height=740,
    returned_objects=["last_object_clicked"],
)

# Debounced Click Selector for Markers
if map_data and map_data.get("last_object_clicked"):
    click = map_data["last_object_clicked"]
    click_key = f"{round(click['lat'], 3)}_{round(click['lng'], 3)}"

    if click_key != st.session_state.last_click:
        st.session_state.last_click = click_key
        closest = min(
            vessels,
            key=lambda v: math.hypot(v["marker_loc"][0] - click["lat"], v["marker_loc"][1] - click["lng"]),
        )
        if math.hypot(closest["marker_loc"][0] - click["lat"], closest["marker_loc"][1] - click["lng"]) < 0.25:
            if st.session_state.selected_vessel_id != closest["id"]:
                st.session_state.selected_vessel_id = closest["id"]
                st.rerun()