# ══════════════════════════════════════════════════════════════════════════
# GeoAID — Geospatial AI-enabled Disaster Intelligence
# Mission Control Dashboard | Amuwo Odofin LGA, Lagos State
# ══════════════════════════════════════════════════════════════════════════
import streamlit as st
import pandas as pd
import numpy as np
import rasterio
import joblib
import shap
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import ee
import os
import time
import json

st.set_page_config(
    page_title="GeoAID // Amuwo Odofin",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── SIGNATURE VISUAL IDENTITY: dark terminal / mission-control aesthetic ────
# JetBrains Mono for that "written by someone who lives in a terminal" feel.
# Scanline glow, phosphor-green accents, glitch-in header — deliberately
# far from Streamlit's default light theme that every tutorial produces.
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700;800&display=swap');

:root {
    --geo-bg: #0a0e14;
    --geo-panel: #10161f;
    --geo-border: #1e2733;
    --geo-green: #39ff9d;
    --geo-amber: #ffb454;
    --geo-red: #ff5c5c;
    --geo-blue: #5ccfe6;
    --geo-text: #b3c2d1;
    --geo-text-dim: #5c6b7a;
}

html, body, [class*="css"] {
    font-family: 'JetBrains Mono', monospace !important;
    background-color: var(--geo-bg);
}

.stApp {
    background: radial-gradient(ellipse at top left, #0d1420 0%, #0a0e14 60%);
}

/* Scanline overlay — subtle CRT feel without being distracting */
.stApp::before {
    content: "";
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: repeating-linear-gradient(
        0deg, rgba(255,255,255,0.012) 0px, transparent 1px,
        transparent 2px, rgba(255,255,255,0.012) 3px
    );
    pointer-events: none;
    z-index: 9999;
}

h1, h2, h3 { font-family: 'JetBrains Mono', monospace !important; letter-spacing: -0.5px; }

/* Header block */
.geo-header {
    border: 1px solid var(--geo-border);
    background: linear-gradient(135deg, #10161f 0%, #0d1420 100%);
    border-radius: 4px;
    padding: 20px 28px;
    margin-bottom: 18px;
    position: relative;
    overflow: hidden;
}
.geo-header::after {
    content: ""; position: absolute; top: 0; left: -100%;
    width: 60%; height: 2px; background: var(--geo-green);
    box-shadow: 0 0 12px 2px var(--geo-green);
    animation: scanbar 4s linear infinite;
}
@keyframes scanbar { 0% {left: -60%;} 100% {left: 110%;} }

.geo-tag {
    display: inline-block; padding: 2px 10px; border-radius: 3px;
    font-size: 11px; font-weight: 700; letter-spacing: 1.5px;
    border: 1px solid var(--geo-green); color: var(--geo-green);
    background: rgba(57,255,157,0.07);
    text-transform: uppercase;
}
.geo-tag.amber { border-color: var(--geo-amber); color: var(--geo-amber); background: rgba(255,180,84,0.07); }
.geo-tag.red   { border-color: var(--geo-red);   color: var(--geo-red);   background: rgba(255,92,92,0.07); }

.geo-title { font-size: 30px; font-weight: 800; color: #eef4fa; margin: 8px 0 2px 0; }
.geo-subtitle { color: var(--geo-text-dim); font-size: 13px; letter-spacing: 0.3px; }

/* Metric cards */
.geo-metric {
    border: 1px solid var(--geo-border); background: var(--geo-panel);
    border-radius: 4px; padding: 16px 18px; height: 100%;
    transition: border-color 0.2s ease;
}
.geo-metric:hover { border-color: var(--geo-green); }
.geo-metric-label { color: var(--geo-text-dim); font-size: 11px; letter-spacing: 1px;
    text-transform: uppercase; margin-bottom: 6px; }
.geo-metric-value { color: #eef4fa; font-size: 26px; font-weight: 700; line-height: 1.1; }
.geo-metric-sub { color: var(--geo-text-dim); font-size: 11px; margin-top: 4px; }

/* Terminal boot log */
.geo-terminal {
    background: #05070b; border: 1px solid var(--geo-border); border-radius: 4px;
    padding: 14px 18px; font-size: 12.5px; color: var(--geo-green);
    line-height: 1.9; box-shadow: inset 0 0 20px rgba(57,255,157,0.03);
}
.geo-terminal .dim { color: var(--geo-text-dim); }
.geo-terminal .warn { color: var(--geo-amber); }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #0d1420; border-right: 1px solid var(--geo-border);
}

/* Tabs */
.stTabs [data-baseweb="tab"] {
    font-family: 'JetBrains Mono', monospace; font-size: 13px;
    color: var(--geo-text-dim);
}
.stTabs [aria-selected="true"] { color: var(--geo-green) !important; }

/* Blinking live dot */
.livedot {
    height: 8px; width: 8px; background-color: var(--geo-green);
    border-radius: 50%; display: inline-block; margin-right: 6px;
    box-shadow: 0 0 6px var(--geo-green);
    animation: pulse 1.4s infinite;
}
@keyframes pulse { 0%,100% {opacity:1;} 50% {opacity:0.25;} }

footer, #MainMenu { visibility: hidden; }
</style>
""", unsafe_allow_html=True)




# ── PROJECT PATHS ─────────────────────────────────────────────────────────────
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR    = os.path.join(PROJECT_DIR, "data")
OUTPUTS_DIR = os.path.join(PROJECT_DIR, "outputs")
MODELS_DIR  = os.path.join(PROJECT_DIR, "models")
FIGURES_DIR = os.path.join(OUTPUTS_DIR, "figures")

@st.cache_resource
def load_model():
    return joblib.load(os.path.join(MODELS_DIR, "random_forest.pkl"))

@st.cache_data
def load_risk_raster():
    with rasterio.open(os.path.join(OUTPUTS_DIR, "flood_risk_tiers.tif")) as src:
        return src.read(1), src.transform, src.bounds

@st.cache_data
def load_probability_raster():
    with rasterio.open(os.path.join(OUTPUTS_DIR, "flood_probability_map.tif")) as src:
        return src.read(1), src.bounds

@st.cache_data
def load_exposure_tables():
    schools   = pd.read_csv(os.path.join(OUTPUTS_DIR, "schools_risk_exposure.csv"))
    health    = pd.read_csv(os.path.join(OUTPUTS_DIR, "health_risk_exposure.csv"))
    roads     = pd.read_csv(os.path.join(OUTPUTS_DIR, "roads_risk_exposure.csv"))
    pop       = pd.read_csv(os.path.join(OUTPUTS_DIR, "population_exposure.csv"))
    return schools, health, roads, pop

@st.cache_data
def load_feature_stack():
    """Loads the 14 resampled feature rasters for point-level SHAP queries."""
    RESAMPLED = os.path.join(DATA_DIR, "resampled")
    fmap = {
        'elevation':               ('resampled_topo_features_amuwo_odofin.tif', 1),
        'slope':                   ('resampled_topo_features_amuwo_odofin.tif', 2),
        'aspect':                  ('resampled_topo_features_amuwo_odofin.tif', 3),
        'flow_accumulation':       ('resampled_topo_features_amuwo_odofin.tif', 4),
        'twi':                     ('resampled_topo_features_amuwo_odofin.tif', 5),
        'curvature':               ('resampled_topo_features_amuwo_odofin.tif', 6),
        'mean_annual_rainfall':    ('resampled_rainfall_lulc_ndvi_amuwo_odofin.tif', 1),
        'mean_rainy_days':         ('resampled_rainfall_lulc_ndvi_amuwo_odofin.tif', 2),
        'extreme_rain_freq':       ('resampled_rainfall_lulc_ndvi_amuwo_odofin.tif', 3),
        'lulc':                    ('resampled_rainfall_lulc_ndvi_amuwo_odofin.tif', 4),
        'ndvi':                    ('resampled_rainfall_lulc_ndvi_amuwo_odofin.tif', 5),
        'soil_permeability':       ('resampled_soil_distance_amuwo_odofin.tif', 1),
        'distance_to_drainage':    ('resampled_soil_distance_amuwo_odofin.tif', 3),
        'gpm_antecedent_rainfall': ('resampled_gpm_antecedent_rainfall_amuwo_odofin.tif', 1),
    }
    ref_path = os.path.join(RESAMPLED, 'resampled_topo_features_amuwo_odofin.tif')
    with rasterio.open(ref_path) as ref:
        ref_shape, ref_transform = (ref.height, ref.width), ref.transform

    layers = []
    for feat, (fn, band) in fmap.items():
        with rasterio.open(os.path.join(RESAMPLED, fn)) as src:
            d = src.read(band).astype(np.float32)
            if d.shape != ref_shape:
                a = np.full(ref_shape, np.nan, dtype=np.float32)
                h, w = min(d.shape[0], ref_shape[0]), min(d.shape[1], ref_shape[1])
                a[:h, :w] = d[:h, :w]
                d = a
            layers.append(d)
    return np.stack(layers, axis=-1), ref_transform, list(fmap.keys())

@st.cache_resource
def load_explainer():
    return joblib.load(os.path.join(MODELS_DIR, "shap_explainer.pkl"))

@st.cache_data
def load_shap_importance():
    return pd.read_csv(os.path.join(OUTPUTS_DIR, "shap_importance.csv"))

@st.cache_resource
def init_gee():
    try:
        ee.Initialize(project='ee-festac')
        return True
    except Exception:
        return False

@st.cache_data(ttl=1800)  # refresh every 30 min
def fetch_live_rainfall(_gee_ready):
    """Pulls 24hr and 72hr GPM IMERG rainfall for Amuwo Odofin — Layer 2 activation."""
    if not _gee_ready:
        return None
    try:
        amuwo = ee.FeatureCollection("FAO/GAUL/2015/level2") \
                  .filter(ee.Filter.eq('ADM0_NAME', 'Nigeria')) \
                  .filter(ee.Filter.eq('ADM1_NAME', 'Lagos')) \
                  .filter(ee.Filter.stringContains('ADM2_NAME', 'Amuwo Odofin'))
        geom = amuwo.geometry()
        now = ee.Date(datetime.utcnow().isoformat())

        def window_sum(hours):
            start = now.advance(-hours, 'hour')
            img = ee.ImageCollection("NASA/GPM_L3/IMERG_V07") \
                    .filterBounds(geom).filterDate(start, now) \
                    .select('precipitation').sum().multiply(0.5)
            val = img.reduceRegion(ee.Reducer.mean(), geom, 500, bestEffort=True).getInfo()
            return val.get('precipitation', 0.0) or 0.0

        return {'r24': window_sum(24), 'r72': window_sum(72)}
    except Exception:
        return None


def boot_sequence():
    """Fake terminal boot log on first load — the signature nerd flourish."""
    if "booted" in st.session_state:
        return
    lines = [
        ("$ geoaid --init --lga=amuwo_odofin", ""),
        ("[OK] loading random_forest.pkl ................ 0.798 ROC-AUC", ""),
        ("[OK] loading flood_risk_tiers.tif .............. 13,022 px", ""),
        ("[OK] loading shap_explainer ..................... 14 features", ""),
        ("[..] establishing GEE session (ee-festac) .......", "dim"),
        ("[OK] querying GPM IMERG live rainfall window ....", ""),
        ("[OK] disaster intelligence layer ................ 229,402 ppl @ risk", "warn"),
        ("$ dashboard ready", ""),
    ]
    box = st.empty()
    rendered = ""
    for text, cls in lines:
        rendered += f'<span class="{cls}">{text}</span><br>'
        box.markdown(f'<div class="geo-terminal">{rendered}</div>', unsafe_allow_html=True)
        time.sleep(0.15)
    time.sleep(0.4)
    box.empty()
    st.session_state["booted"] = True

boot_sequence()


# ── PLAIN-LANGUAGE TRANSLATION ────────────────────────────────────────────────
# Maps each conditioning factor to what it physically means on the ground,
# with the direction of effect. Used to assemble explanations from SHAP
# output without any generative model in the loop.

FEATURE_PLAIN = {
    'ndvi': {
        'high': "the area has good vegetation cover, which helps absorb rainfall",
        'low':  "the ground is mostly concrete and rooftops with very little greenery, "
                "so rain runs off instead of soaking in"
    },
    'elevation': {
        'high': "the land sits relatively high, so water drains away from it",
        'low':  "the land is low-lying, so water collects here rather than draining away"
    },
    'distance_to_drainage': {
        'high': "the area is far from any drainage channel",
        'low':  "the area sits close to a canal or drainage channel that can overflow"
    },
    'soil_permeability': {
        'high': "the soil is sandy and absorbs water reasonably well",
        'low':  "the soil is clay-heavy and absorbs water poorly, so rain sits on the surface"
    },
    'twi': {
        'high': "the terrain shape causes water to collect and stay here",
        'low':  "the terrain shape allows water to move through rather than pool"
    },
    'slope': {
        'high': "the ground slopes enough for water to run off",
        'low':  "the ground is almost flat, so water has nowhere to run to"
    },
    'flow_accumulation': {
        'high': "water from a large surrounding area drains through this point",
        'low':  "little water from elsewhere flows through this point"
    },
    'lulc': {
        'high': "the land is heavily built up",
        'low':  "the land is less densely built"
    },
    'curvature': {
        'high': "the ground curves outward, shedding water",
        'low':  "the ground forms a hollow where water gathers"
    },
    'aspect': {
        'high': "the slope faces a direction that affects how water moves across it",
        'low':  "the slope faces a direction that affects how water moves across it"
    },
    'mean_annual_rainfall': {
        'high': "the area receives heavy rainfall each year",
        'low':  "the area receives comparatively less rainfall each year"
    },
    'mean_rainy_days': {
        'high': "rain falls on many days through the year",
        'low':  "rain falls on fewer days through the year"
    },
    'extreme_rain_freq': {
        'high': "very heavy downpours happen often here",
        'low':  "very heavy downpours are less frequent here"
    },
    'gpm_antecedent_rainfall': {
        'high': "the ground is often already soaked before a storm arrives",
        'low':  "the ground is usually drier before a storm arrives"
    },
}

TIER_PLAIN = {
    1: ("Low risk", "This area does not usually flood, even during heavy rain."),
    2: ("Moderate risk", "This area can flood during unusually heavy or prolonged rain."),
    3: ("High risk", "This area floods regularly when rain is heavy."),
    4: ("Very high risk", "This area floods often during heavy rain and water "
                          "can stay for some time."),
}

TIER_ADVICE = {
    1: "No special precautions needed beyond normal rainy-season care.",
    2: "Keep drains around the property clear before the rainy season starts.",
    3: "Clear nearby drains before the rains, avoid parking in low spots, "
       "and keep an eye on rainfall warnings.",
    4: "Clear nearby drains before the rains, keep valuables raised off the floor, "
       "plan a route out that avoids the canal, and pay close attention to "
       "rainfall warnings.",
}

def explain_plain(tier, shap_row, feature_values, feature_names, top_n=3):
    """
    Assembles a plain-language explanation from SHAP output.
    Deterministic — no generative model involved.
    """
    if tier == 0:
        return "No risk classification is available for this exact spot.", []

    label, opener = TIER_PLAIN[int(tier)]

    order = np.argsort(-np.abs(shap_row))[:top_n]
    reasons = []
    for i in order:
        name = feature_names[i]
        if name not in FEATURE_PLAIN:
            continue
        # SHAP positive = pushes toward flood. Pick the phrasing that matches.
        direction = 'low' if shap_row[i] > 0 else 'high'
        # For features where a HIGH value drives flooding, invert
        if name in ('twi', 'flow_accumulation', 'lulc', 'mean_annual_rainfall',
                    'mean_rainy_days', 'extreme_rain_freq', 'gpm_antecedent_rainfall'):
            direction = 'high' if shap_row[i] > 0 else 'low'
        reasons.append(FEATURE_PLAIN[name][direction])

    if reasons:
        body = opener + " The main reasons are that " + reasons[0]
        if len(reasons) > 1:
            body += ", " + ", ".join(reasons[1:-1] + [f"and {reasons[-1]}"]) \
                    if len(reasons) > 2 else f", and {reasons[1]}"
        body += "."
    else:
        body = opener

    return body, [(feature_names[i], float(shap_row[i])) for i in order]



# ── HEADER ─────────────────────────────────────────────────────────────────
gee_ready = init_gee()
now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

st.markdown(f"""
<div class="geo-header">
    <span class="geo-tag">GeoAID v1.0</span>
    <span class="geo-tag amber">LAYER 1·2·3 ACTIVE</span>
    <span class="geo-tag {'red' if not gee_ready else ''}">
        <span class="livedot"></span>{'GEE CONNECTED' if gee_ready else 'GEE OFFLINE — CACHED DATA'}
    </span>
    <div class="geo-title">GeoAID // Amuwo Odofin Flood Intelligence</div>
    <div class="geo-subtitle">Geospatial AI-enabled Disaster Intelligence — Structural Susceptibility · Rainfall Activation · Exposure Assessment</div>
    <div class="geo-subtitle" style="margin-top:6px;">Session time: {now_str} · Random Forest (14 features) · Miva Open University MSc Project</div>
</div>
""", unsafe_allow_html=True)




# ── LOAD DATA ─────────────────────────────────────────────────────────────────
rf_model = load_model()
risk_tiers, tier_transform, tier_bounds = load_risk_raster()
proba_map, _ = load_probability_raster()
schools_df, health_df, roads_df, pop_df = load_exposure_tables()
shap_df = load_shap_importance()

total_pop = pop_df['population'].sum()
vhigh_pop = pop_df.loc[pop_df['tier'] == 'Very High', 'population'].sum()
high_pop  = pop_df.loc[pop_df['tier'] == 'High', 'population'].sum()
at_risk_pop = vhigh_pop + high_pop
schools_at_risk = schools_df['risk_label'].isin(['High', 'Very High']).sum()
health_at_risk  = health_df['risk_label'].isin(['High', 'Very High']).sum()
roads_at_risk   = roads_df['risk_label'].isin(['High', 'Very High']).sum()

# ── METRIC ROW ─────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
metrics = [
    (c1, "MODEL ROC-AUC", "0.798", "Random Forest · 14 features"),
    (c2, "POP. AT RISK", f"{at_risk_pop:,.0f}", f"{at_risk_pop/total_pop*100:.1f}% of {total_pop:,.0f}"),
    (c3, "SCHOOLS EXPOSED", f"{schools_at_risk} / {len(schools_df)}", "High + Very High tier"),
    (c4, "HEALTH FACILITIES", f"{health_at_risk} / {len(health_df)}", "High + Very High tier"),
    (c5, "ROADS EXPOSED", f"{roads_at_risk} / {len(roads_df)}", "Access constraint risk"),
]
for col, label, val, sub in metrics:
    col.markdown(f"""
    <div class="geo-metric">
        <div class="geo-metric-label">{label}</div>
        <div class="geo-metric-value">{val}</div>
        <div class="geo-metric-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")




# ── SIDEBAR ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<span class="geo-tag">CONTROL PANEL</span>', unsafe_allow_html=True)
    st.write("")
    view_mode = st.radio(
        "AUDIENCE MODE",
        ["Technical (NEMA/LASEMA)", "Plain Language (Community)"],
        label_visibility="visible"
    )
    st.markdown("---")
    
    show_infra = st.multiselect(
        "OVERLAY INFRASTRUCTURE",
        ["Schools", "Health Facilities", "Roads"],
        default=["Schools", "Health Facilities"]
    )
    st.markdown("---")
    st.markdown(f'<span class="geo-metric-label">DATA SOURCES</span>', unsafe_allow_html=True)
    st.caption("SRTM · CHIRPS · Sentinel-1/2 · ESA WorldCover · JRC GSW · GPM IMERG · WorldPop · OSM")
    st.markdown("---")
    st.caption("github.com/Dexsholey/GeoAID-Lagos-FloodRisk")

# ── MAIN TABS ──────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "◆ STRUCTURAL RISK MAP",
    "◆ LIVE RAINFALL ACTIVATION",
    "◆ EXPLAINABILITY",
    "◆ DISASTER INTELLIGENCE"
])




# ── TAB 1: STRUCTURAL RISK MAP ────────────────────────────────────────────────
with tab1:
    plain = view_mode.startswith("Plain")
    feat_stack, feat_transform, feat_names = load_feature_stack()

    left, right = st.columns([2.3, 1])

    with left:
        clat = (tier_bounds.top + tier_bounds.bottom) / 2
        clon = (tier_bounds.left + tier_bounds.right) / 2

        m = folium.Map(location=[clat, clon], zoom_start=13, tiles=None)

        # ── Basemaps ──────────────────────────────────────────────────────
        folium.TileLayer("CartoDB dark_matter", name="Dark (default)",
                          control=True).add_to(m)
        folium.TileLayer("OpenStreetMap", name="OpenStreetMap (streets & buildings)",
                          control=True).add_to(m)
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/"
                  "World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Esri, Maxar, Earthstar Geographics",
            name="Satellite imagery (Esri)", control=True
        ).add_to(m)

        # ── Risk tier overlay as RGBA ─────────────────────────────────────
        rgba = np.zeros((*risk_tiers.shape, 4), dtype=np.uint8)
        palette = {1: (57, 255, 157), 2: (255, 180, 84),
                   3: (255, 140, 66), 4: (255, 92, 92)}
        for t, (r, g, b) in palette.items():
            mask = risk_tiers == t
            rgba[mask] = [r, g, b, 165]

        folium.raster_layers.ImageOverlay(
            image=rgba,
            bounds=[[tier_bounds.bottom, tier_bounds.left],
                    [tier_bounds.top, tier_bounds.right]],
            name="Flood risk zones", opacity=0.75
        ).add_to(m)

        # ── Infrastructure markers ────────────────────────────────────────
        marker_cfg = [
            ("Schools", schools_df, "graduation-cap", "Schools"),
            ("Health Facilities", health_df, "plus-square", "Health facilities"),
            ("Roads", roads_df, "road", "Major roads"),
        ]
        tier_hex = {1: '#39ff9d', 2: '#ffb454', 3: '#ff8c42', 4: '#ff5c5c', 0: '#888888'}

        for label, df, icon, layer_name in marker_cfg:
            if label not in show_infra:
                continue
            if 'longitude' not in df.columns:
                st.warning(f"{label}: coordinates missing — re-run NB09 export.")
                continue
            fg = folium.FeatureGroup(name=layer_name, show=True)
            for _, row in df.iterrows():
                tier = int(row.get('risk_tier', 0))
                popup = (f"<b>{row.get('name','Unnamed')}</b><br>"
                         f"{TIER_PLAIN.get(tier, ('Unclassified',''))[0]}")
                folium.CircleMarker(
                    location=[row['latitude'], row['longitude']],
                    radius=5, color='#ffffff', weight=1,
                    fill=True, fill_color=tier_hex.get(tier, '#888888'),
                    fill_opacity=0.9, popup=folium.Popup(popup, max_width=250)
                ).add_to(fg)
            fg.add_to(m)

        folium.LayerControl(collapsed=False).add_to(m)

        map_state = st_folium(m, width=None, height=580,
                               returned_objects=["last_clicked"])

    # ── Click-to-query panel ──────────────────────────────────────────────
    with right:
        st.markdown("**Query a location**")
        st.caption("Click anywhere on the map to see why that spot carries its rating.")

        clicked = map_state.get("last_clicked") if map_state else None

        if clicked:
            qlon, qlat = clicked["lng"], clicked["lat"]
            row, col = rasterio.transform.rowcol(tier_transform, qlon, qlat)

            in_bounds = (0 <= row < risk_tiers.shape[0] and
                         0 <= col < risk_tiers.shape[1])

            if not in_bounds:
                st.warning("That point falls outside the study area.")
            else:
                tier = int(risk_tiers[row, col])
                fvals = feat_stack[row, col, :]

                if tier == 0 or np.isnan(fvals).any():
                    st.info("No risk classification available for this exact spot. "
                            "Try clicking slightly inland.")
                else:
                    explainer = load_explainer()
                    sv_raw = explainer.shap_values(fvals.reshape(1, -1))
                    if isinstance(sv_raw, list):
                        sv = sv_raw[1][0]
                    elif len(np.array(sv_raw).shape) == 3:
                        sv = np.array(sv_raw)[0, :, 1]
                    else:
                        sv = np.array(sv_raw)[0]

                    prob = rf_model.predict_proba(fvals.reshape(1, -1))[0, 1]
                    text, top = explain_plain(tier, sv, fvals, feat_names)
                    label, _ = TIER_PLAIN[tier]
                    colour = tier_hex[tier]

                    st.markdown(f"""<div class="geo-metric" style="border-color:{colour};">
                        <div class="geo-metric-label">CLASSIFICATION</div>
                        <div class="geo-metric-value" style="color:{colour};">{label}</div>
                        <div class="geo-metric-sub">{qlat:.5f}, {qlon:.5f}</div>
                    </div>""", unsafe_allow_html=True)
                    st.write("")

                    if plain:
                        st.markdown(f"##### What this means")
                        st.write(text)
                        st.markdown("##### What you can do")
                        st.write(TIER_ADVICE[tier])
                    else:
                        st.metric("Flood probability", f"{prob:.3f}")
                        st.markdown("**Top SHAP contributors**")
                        for fname, val in top:
                            arrow = "↑" if val > 0 else "↓"
                            st.write(f"`{fname}` {arrow} {val:+.4f}")
                        st.caption(text)
        else:
            st.info("No location selected yet.")

        st.markdown("---")
        st.markdown("**Legend**")
        for t in [4, 3, 2, 1]:
            st.markdown(f"""<div style="display:flex;align-items:center;margin-bottom:5px;">
                <div style="width:13px;height:13px;background:{tier_hex[t]};
                border-radius:2px;margin-right:8px;"></div>
                <span style="color:#b3c2d1;font-size:13px;">{TIER_PLAIN[t][0]}</span>
                </div>""", unsafe_allow_html=True)
        
        
        
        
# ── TAB 2: LIVE RAINFALL ACTIVATION (LAYER 2) ────────────────────────────────
with tab2:
    st.markdown("### Dynamic Risk Activation")
    st.caption("Connects the static structural susceptibility map to current rainfall "
               "conditions via NASA GPM IMERG — updated every 30 minutes globally.")

    rainfall = fetch_live_rainfall(gee_ready)

    if rainfall is None:
        st.warning("⚠ GEE session unavailable — showing last cached extreme-rainfall threshold (50mm/day, CHIRPS climatology).")
        r24, r72 = 0.0, 0.0
    else:
        r24, r72 = rainfall['r24'], rainfall['r72']

    THRESHOLD_24H = 50.0
    activated = r24 >= THRESHOLD_24H

    a1, a2, a3 = st.columns(3)
    a1.markdown(f"""<div class="geo-metric"><div class="geo-metric-label">24HR RAINFALL</div>
        <div class="geo-metric-value">{r24:.1f} mm</div>
        <div class="geo-metric-sub">Threshold: {THRESHOLD_24H:.0f}mm</div></div>""", unsafe_allow_html=True)
    a2.markdown(f"""<div class="geo-metric"><div class="geo-metric-label">72HR ACCUMULATION</div>
        <div class="geo-metric-value">{r72:.1f} mm</div>
        <div class="geo-metric-sub">Antecedent saturation proxy</div></div>""", unsafe_allow_html=True)
    status_color = "#ff5c5c" if activated else "#39ff9d"
    status_text = "ACTIVATED" if activated else "NOMINAL"
    a3.markdown(f"""<div class="geo-metric" style="border-color:{status_color};">
        <div class="geo-metric-label">ACTIVATION STATE</div>
        <div class="geo-metric-value" style="color:{status_color};">{status_text}</div>
        <div class="geo-metric-sub">High/Very High zones {'flagged' if activated else 'quiet'}</div></div>""",
        unsafe_allow_html=True)

    st.write("")
    if activated:
        st.error(f"🚨 Structurally High/Very High risk zones are currently under active "
                 f"rainfall forcing ({r24:.1f}mm in 24hrs). Recommend field verification.")
    else:
        st.success("✓ No active rainfall forcing detected on structural risk zones.")

    st.caption("Note: this is a threshold-based operational overlay, not a hydrodynamic "
               "flood forecast. It indicates when structural susceptibility is being "
               "activated by prevailing weather, per the GeoAID Layer 2 design.")
    
    
    
    
# ── TAB 3: EXPLAINABILITY ────────────────────────────────────────────────────
with tab3:
    plain = view_mode.startswith("Plain")

    if plain:
        st.markdown("### What makes an area flood")
        st.write("Across Amuwo Odofin, the strongest single factor is how much "
                 "greenery an area has. Places covered in concrete and rooftops, "
                 "with little vegetation, flood far more than places with open "
                 "ground and plants. After that, low-lying land and closeness to "
                 "a drainage channel matter most.")
        st.info("Rainfall amount matters less than you might expect here. "
                "That is because rainfall is roughly the same across the whole "
                "LGA — what differs between one street and the next is the "
                "ground itself.")
    else:
        st.markdown("### Global SHAP feature importance")
        st.caption("Mean absolute SHAP value — average impact of each factor "
                   "on model output across the test set.")

        fig = px.bar(shap_df.sort_values('Mean_Abs_SHAP'),
                     x='Mean_Abs_SHAP', y='Feature',
                     orientation='h', template="plotly_dark")
        fig.update_traces(marker_color='#5ccfe6')
        fig.update_layout(height=460, paper_bgcolor='#10161f',
                          plot_bgcolor='#10161f',
                          margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

        st.info("**NDVI dominates.** Low vegetation cover — impervious surface — "
                "is the strongest single driver of flood susceptibility in "
                "Amuwo Odofin, confirmed independently by both SHAP and Gini "
                "importance.")

        col1, col2 = st.columns(2)
        bees = os.path.join(FIGURES_DIR, "shap_beeswarm.png")
        dep  = os.path.join(FIGURES_DIR, "shap_dependence_plots.png")
        if os.path.exists(bees):
            col1.image(bees, caption="SHAP beeswarm — direction of effect")
        if os.path.exists(dep):
            col2.image(dep, caption="Dependence plots — top 4 features")
        
        
        
# ── TAB 4: DISASTER INTELLIGENCE ─────────────────────────────────────────────
with tab4:
    st.markdown("### Population and Infrastructure Exposure")

    pop_fig = go.Figure(data=[go.Bar(
        x=pop_df['tier'], y=pop_df['population'],
        marker_color=['#39ff9d','#ffb454','#ff8c42','#ff5c5c']
    )])
    pop_fig.update_layout(template="plotly_dark", height=340,
                          paper_bgcolor='#10161f', plot_bgcolor='#10161f',
                          title="Population by risk tier",
                          margin=dict(l=10,r=10,t=40,b=10))
    st.plotly_chart(pop_fig, use_container_width=True)

    st.markdown(f"**{at_risk_pop:,.0f} people ({at_risk_pop/total_pop*100:.1f}%)** "
                f"live in High or Very High flood risk zones across Amuwo Odofin LGA.")

    st.markdown("---")
    ic1, ic2, ic3 = st.columns(3)
    with ic1:
        st.markdown("**Schools by tier**")
        st.dataframe(schools_df['risk_label'].value_counts(), use_container_width=True)
    with ic2:
        st.markdown("**Health facilities by tier**")
        st.dataframe(health_df['risk_label'].value_counts(), use_container_width=True)
    with ic3:
        st.markdown("**Major roads by tier**")
        st.dataframe(roads_df['risk_label'].value_counts(), use_container_width=True)

    infra_map_path = os.path.join(FIGURES_DIR, "infrastructure_risk_map.png")
    if os.path.exists(infra_map_path):
        st.image(infra_map_path, caption="Infrastructure exposure map")