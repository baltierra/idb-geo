import streamlit as st
import pandas as pd
import datetime as dt
import numpy as np
import ee
import geemap
from sklearn.linear_model import LinearRegression
from streamlit_folium import st_folium
import folium
from folium.plugins import DualMap

# ─── INIT ────────────────────────────────────────────────────────────────
st.set_page_config(layout="wide", page_title="Bridge Progress Tracker")
ee.Initialize()

# Coordinates for your bridge:
BRIDGE_LAT, BRIDGE_LON = -41.795582772327116, -73.5238575107115
AOI_BUFFER_KM = 2  # buffer radius

# ─── FIXED PARAMETERS ────────────────────────────────────────────────────
# Fixed start and current dates (no date inputs)
t0 = dt.date(2019, 1, 19)
t1 = dt.date(2025, 2, 26)

# Sidebar: only current percentage
st.sidebar.header("Configuration")
current_pct = st.sidebar.slider(
    "Current % complete",
    min_value=0, max_value=100, value=50
)

# ─── BUILD AOI ───────────────────────────────────────────────────────────
point = ee.Geometry.Point([BRIDGE_LON, BRIDGE_LAT])
aoi = point.buffer(AOI_BUFFER_KM * 1000)

# ─── CLOUD‑MASKED MOSAIC ─────────────────────────────────────────────────
def mask_s2(img):
    qa = img.select("QA60")
    cloud_bits = (1 << 10) | (1 << 11)
    mask = qa.bitwiseAnd(cloud_bits).eq(0)
    return img.updateMask(mask).select(["B4","B3","B2"]).divide(10000)

def mosaic_for(date_obj):
    date = ee.Date(date_obj.isoformat())
    coll = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
          .filterDate(date, date.advance(1, "month"))
          .filterBounds(aoi)
          .map(mask_s2)
    )
    return coll.median().clip(aoi)

@st.cache_data(show_spinner=False)
def get_mosaics():
    m0 = mosaic_for(t0)
    m1 = mosaic_for(t1)
    return m0, m1

m0, m1 = get_mosaics()

# ─── PREDICT FINISH DATE ──────────────────────────────────────────────────
days_elapsed = (t1 - t0).days or 1
slope = current_pct / days_elapsed
days_to_finish = int((100 - current_pct) / slope) if slope > 0 else None
pred_date = t1 + dt.timedelta(days=days_to_finish) if days_to_finish else None

# ─── RENDER MAP ──────────────────────────────────────────────────────────
st.title("🌉 Chile's Chacao Bridge - Construction Progress")
st.markdown(
    """
    In Chile's Los Lagos Region, the Chacao Bridge has been under construction since December 2018.
    This bridge will finally connect Chiloé Island to the mainland—a journey that is currently only possible by ferry.
    Below are two satellite images taken on different dates that show the construction progress.
    According to local authorities, the most recent image reflects approximately 50\% completion.

    Using this data, we applied a simple predictive model using Python's Scikit-learn to estimate the number of construction days remaining.
    You can adjust the slider to see how the prediction changes based on different inputs.
    """
)
vis = {"min":0, "max":0.3}

# EE tile URLs
mapid0 = ee.Image(m0).getMapId(vis)
mapid1 = ee.Image(m1).getMapId(vis)

# Build TileLayers
tile0 = folium.TileLayer(
    tiles=mapid0["tile_fetcher"].url_format,
    attr="Google Earth Engine",
    name="T₀",
    overlay=True,
    control=False,
)
tile1 = folium.TileLayer(
    tiles=mapid1["tile_fetcher"].url_format,
    attr="Google Earth Engine",
    name="T₁",
    overlay=True,
    control=False,
)

# Create DualMap and add layers
dual = DualMap(
    location=[BRIDGE_LAT, BRIDGE_LON],
    zoom_start=13,
    tiles="CartoDB.Positron",
)
tile0.add_to(dual.m1)
tile1.add_to(dual.m2)

st.subheader(f"AOI (2km buffer around bridge)")
st_folium(dual, width=800, height=500)

# ─── METRICS & CHARTS ─────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
col1.metric("Start date", t0.strftime("%Y-%m-%d"))
col2.metric("Current date", t1.strftime("%Y-%m-%d"))
col3.metric("Current advance", f"{current_pct}%")

if pred_date:
    st.sidebar.metric("⏳ Predicted completion", pred_date.strftime("%Y‑%m‑%d"))
    st.sidebar.metric("Days remaining", days_to_finish)

if st.checkbox("Show extrapolation chart"):
    df = pd.DataFrame({
        "date": [t0, t1],
        "pct": [0, current_pct]
    })
    df["ordinal"] = df["date"].map(dt.date.toordinal)
    model = LinearRegression().fit(
        df[["ordinal"]], df[["pct"]]
    )
    rng = pd.date_range(t0, pred_date, freq="D")
    ords = rng.map(dt.date.toordinal).to_numpy().reshape(-1,1)
    preds = model.predict(ords)
    chart_df = pd.DataFrame({"Date": rng, "Pct": np.ravel(preds)}).set_index("Date")
    st.line_chart(chart_df)
