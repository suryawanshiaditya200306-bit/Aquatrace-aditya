import math
import folium
from folium import plugins
import streamlit as st
from streamlit_folium import st_folium

# 1. Full-Screen Page Configuration
st.set_page_config(page_title="AquaTrace | Orbital View", layout="wide", initial_sidebar_state="expanded")

# 2. Advanced HUD Styling & Canvas Optimization
st.markdown("""
<style>
.block-container { padding: 0rem !important; margin: 0rem !important; max-width: 100% !important; overflow: hidden; }
header { display: none !important; }
footer { display: none !important; }
.stApp { background-color: #000000; }
[data-testid="stSidebar"] { 
    background-color: #0B1120; 
    border-right: 1px solid #1E293B;
    box-shadow: 2px 0px 20px rgba(0,0,0,0.8);
}
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0B1120; }
::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# 3. Session State Management
if "selected_vessel_id" not in st.session_state:
    st.session_state.selected_vessel_id = None

# Telemetry and Geospatial Polygons
vessels = [
    {
        "id": "v1", "name": "MT Sagar Ratna", "mmsi": "419000123", "type": "Crude Oil Tanker",
        "speed": "11.4 kts", "confidence": "96.2%", "area": "1.2 sq km", "marker_loc": [17.65, 83.66],
        "spill": [[17.67, 83.63], [17.71, 83.65], [17.69, 83.69], [17.65, 83.66]],
        "path": [[17.35, 83.35], [17.46, 83.42], [17.58, 83.52], [17.69, 83.66], [17.78, 83.79]]
    },
    {
        "id": "v2", "name": "MV Crimson Tide", "mmsi": "419000888", "type": "Bulk Carrier",
        "speed": "9.8 kts", "confidence": "91.5%", "area": "0.8 sq km", "marker_loc": [16.98, 82.35],
        "spill": [[16.95, 82.30], [17.00, 82.32], [16.99, 82.38], [16.96, 82.36]],
        "path": [[16.70, 82.10], [16.85, 82.25], [16.98, 82.35], [17.15, 82.50]]
    },
    {
        "id": "v3", "name": "Black Pearl (Rogue)", "mmsi": "UNKNOWN", "type": "Unregistered Tanker",
        "speed": "14.1 kts", "confidence": "98.9%", "area": "2.4 sq km", "marker_loc": [18.50, 84.80],
        "spill": [[18.48, 84.75], [18.55, 84.77], [18.52, 84.85], [18.49, 84.82]],
        "path": [[18.10, 84.40], [18.30, 84.60], [18.50, 84.80], [18.75, 85.05]]
    },
    {
        "id": "v4", "name": "Oceanic Voyager", "mmsi": "419000456", "type": "Chemical Tanker",
        "speed": "12.3 kts", "confidence": "89.4%", "area": "0.5 sq km", "marker_loc": [20.15, 86.75],
        "spill": [[20.12, 86.70], [20.18, 86.72], [20.16, 86.80], [20.13, 86.78]],
        "path": [[19.80, 86.40], [19.95, 86.60], [20.15, 86.75], [20.40, 86.95]]
    }
]

# 4. AquaTrace Sidebar HUD
active_vessel = next((v for v in vessels if v["id"] == st.session_state.selected_vessel_id), None)

with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #00FFFF; letter-spacing: 2px; font-weight: 800;'>AQUATRACE</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748B; font-size: 12px; margin-top: -15px;'>ORBITAL FORENSICS ENGINE</p>", unsafe_allow_html=True)
    st.markdown("<hr style='border-color: #1E293B; margin-top: 5px; margin-bottom: 20px;'>", unsafe_allow_html=True)
    
    if active_vessel:
        main_box_html = (
            "<div style='background: linear-gradient(145deg, #1E293B 0%, #0F172A 100%); padding: 18px; border-radius: 10px; border: 1px solid #334155; border-left: 5px solid #FF004D; box-shadow: 0 10px 20px rgba(0,0,0,0.6); margin-bottom: 20px;'>"
            "<p style='color: #FF004D; font-size: 11px; font-weight: bold; letter-spacing: 1.5px; margin-bottom: 0;'>⚠️ VIOLATION DETECTED</p>"
            f"<h3 style='color: #F8FAFC; margin-top: 5px; margin-bottom: 15px; font-size: 20px;'>{active_vessel['name']}</h3>"
            "<div style='display: flex; justify-content: space-between; border-bottom: 1px solid #334155; padding-bottom: 6px; margin-bottom: 6px; font-size: 14px;'>"
            "<span style='color: #94A3B8;'>MMSI Registry</span>"
            f"<span style='color: #E2E8F0; font-family: monospace;'>{active_vessel['mmsi']}</span>"
            "</div>"
            "<div style='display: flex; justify-content: space-between; border-bottom: 1px solid #334155; padding-bottom: 6px; margin-bottom: 6px; font-size: 14px;'>"
            "<span style='color: #94A3B8;'>Vessel Class</span>"
            f"<span style='color: #E2E8F0;'>{active_vessel['type']}</span>"
            "</div>"
            "<div style='display: flex; justify-content: space-between; padding-bottom: 6px; font-size: 14px;'>"
            "<span style='color: #94A3B8;'>Transit Speed</span>"
            f"<span style='color: #E2E8F0;'>{active_vessel['speed']}</span>"
            "</div>"
            "</div>"
        )
        st.markdown(main_box_html, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            confidence_html = (
                "<div style='background-color: #0F172A; padding: 12px; border-radius: 8px; border: 1px solid #1E293B; text-align: center;'>"
                "<p style='color: #94A3B8; font-size: 11px; margin-bottom: 0;'>CONFIDENCE</p>"
                f"<h4 style='color: #00FFFF; margin-top: 0;'>{active_vessel['confidence']}</h4>"
                "</div>"
            )
            st.markdown(confidence_html, unsafe_allow_html=True)
            
        with col2:
            area_html = (
                "<div style='background-color: #0F172A; padding: 12px; border-radius: 8px; border: 1px solid #1E293B; text-align: center;'>"
                "<p style='color: #94A3B8; font-size: 11px; margin-bottom: 0;'>SPILL AREA</p>"
                f"<h4 style='color: #FF004D; margin-top: 0;'>{active_vessel['area']}</h4>"
                "</div>"
            )
            st.markdown(area_html, unsafe_allow_html=True)

        st.write("")

        terminal_html = (
            "<div style='background-color: #020617; padding: 12px; border-radius: 6px; font-family: monospace; font-size: 11px; color: #4ADE80; border: 1px solid #166534; box-shadow: inset 0 0 10px rgba(0,0,0,0.8);'>"
            "> INITIALIZING SAR CORRELATION...<br>"
            f"> FETCHING AIS TELEMETRY [{active_vessel['mmsi']}]...<br>"
            "> CALCULATING TRAJECTORY OVERLAP...<br>"
            "> <b>MATCH CONFIRMED: SPATIAL-TEMPORAL OVERLAP VERIFIED.</b>"
            "</div>"
        )
        st.markdown(terminal_html, unsafe_allow_html=True)

        st.write("")
        
        dossier = f"AQUATRACE INCIDENT DOSSIER\nTarget: {active_vessel['name']}\nMMSI: {active_vessel['mmsi']}\nMatch Confidence: {active_vessel['confidence']}\nCoordinates: {active_vessel['marker_loc']}"
        st.download_button("📥 EXPORT LEGAL DOSSIER", data=dossier, file_name=f"aquatrace_evidence_{active_vessel['id']}.txt", type="primary", use_container_width=True)
        
        if st.button("✖ DISENGAGE TARGET", use_container_width=True):
            st.session_state.selected_vessel_id = None
            st.rerun()

    else:
        idle_html = (
            "<div style='text-align: center; padding: 30px 10px;'>"
            "<p style='font-size: 40px; margin-bottom: 0;'>🛰️</p>"
            "<h4 style='color: #94A3B8; font-weight: 400;'>RADAR ACTIVE</h4>"
            "<p style='color: #475569; font-size: 13px;'>Monitoring East Coast Corridor.<br>Select a red anomaly marker on the map to extract forensic telemetry.</p>"
            "</div>"
        )
        st.markdown(idle_html, unsafe_allow_html=True)

# 5. Initialize Satellite Base Map
m = folium.Map(
    location=[18.50, 84.50], 
    zoom_start=7, 
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr="Esri"
)

# 6. Render Detection Layers & Dynamic Traces
for v in vessels:
    is_selected = (v["id"] == st.session_state.selected_vessel_id)

    folium.Polygon(
        locations=v["spill"], color="#FF004D", fill=True, fill_color="#FF004D", fill_opacity=0.6,
    ).add_to(m)

    if is_selected:
        plugins.AntPath(
            locations=v["path"], color="#00FFFF", weight=4, dash_array=[15, 20], delay=800,
        ).add_to(m)
    else:
        folium.PolyLine(
            locations=v["path"], color="#94A3B8", weight=2, opacity=0.3, dash_array="4, 12"
        ).add_to(m)

    folium.Marker(
        location=v["marker_loc"],
        icon=folium.Icon(color="red" if not is_selected else "blue", icon="screenshot"),
    ).add_to(m)

# 7. Render Streamlit Map Element
map_data = st_folium(
    m, 
    key="aquatrace_map",
    use_container_width=True, 
    height=850, 
    returned_objects=["last_object_clicked"] 
)

# 8. Interactive Spatial Intersect Processing
if map_data and map_data.get("last_object_clicked"):
    clicked_lat = map_data["last_object_clicked"]["lat"]
    clicked_lng = map_data["last_object_clicked"]["lng"]
    
    for v in vessels:
        dist = math.hypot(v["marker_loc"][0] - clicked_lat, v["marker_loc"][1] - clicked_lng)
        if dist < 0.1:
            if st.session_state.selected_vessel_id != v["id"]:
                st.session_state.selected_vessel_id = v["id"]
                st.rerun()
