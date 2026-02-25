import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="NOC KPI Dashboard", layout="wide")

st.title("📊 NOC KPI Monitoring Dashboard")

# ==============================
# LOAD DATA
# ==============================

@st.cache_data
def load_data():
    df = pd.read_csv("kpi_data.csv")
    df.columns = df.columns.str.strip().str.lower()
    return df

try:
    df = load_data()
except Exception as e:
    st.error("Error loading CSV file")
    st.stop()

st.write("Detected Columns:", df.columns.tolist())

# ==============================
# VALIDASI KOLOM WAJIB
# ==============================

required_columns = ["date", "site", "availability", "traffic_gb", "lat", "lon"]

for col in required_columns:
    if col not in df.columns:
        st.error(f"Required column '{col}' not found in dataset")
        st.stop()

# ==============================
# DATA PREPARATION
# ==============================

df["date"] = pd.to_datetime(df["date"], errors="coerce")

df = df.dropna(subset=["date"])

# ==============================
# SIDEBAR FILTER
# ==============================

st.sidebar.header("Filter")

site_list = ["All"] + sorted(df["site"].dropna().unique())
selected_site = st.sidebar.selectbox("Select Site", site_list)

date_range = st.sidebar.date_input(
    "Select Date Range",
    [df["date"].min(), df["date"].max()]
)

# Filter logic
if selected_site != "All":
    df = df[df["site"] == selected_site]

df = df[
    (df["date"] >= pd.to_datetime(date_range[0])) &
    (df["date"] <= pd.to_datetime(date_range[1]))
]

# ==============================
# KPI SUMMARY
# ==============================

col1, col2, col3 = st.columns(3)

col1.metric("Total Sites", df["site"].nunique())
col2.metric("Avg Availability", f"{df['availability'].mean():.2f}%")
col3.metric("Total Traffic (GB)", f"{df['traffic_gb'].sum():,.0f}")

st.divider()

# ==============================
# CONGESTION DETECTION
# ==============================

st.subheader("🚨 Congestion Detection")

congestion_threshold = st.slider("Availability Threshold (%)", 90, 100, 95)

df["congestion"] = df["availability"] < congestion_threshold

congestion_sites = df[df["congestion"] == True]

st.write("Total Congested Records:", congestion_sites.shape[0])

if not congestion_sites.empty:
    st.dataframe(congestion_sites)
else:
    st.success("No congestion detected 🎉")

st.divider()

# ==============================
# KPI TREND
# ==============================

st.subheader("📈 Availability Trend")

trend_df = df.groupby("date")["availability"].mean().reset_index()

fig_trend = px.line(
    trend_df,
    x="date",
    y="availability",
    markers=True
)

st.plotly_chart(fig_trend, use_container_width=True)

# ==============================
# GEO MAP
# ==============================

st.subheader("🗺 Site Location Map")

map_df = df.dropna(subset=["lat", "lon"])

if not map_df.empty:
    fig_map = px.scatter_mapbox(
        map_df,
        lat="lat",
        lon="lon",
        color="availability",
        hover_name="site",
        zoom=5,
        height=600
    )

    fig_map.update_layout(mapbox_style="open-street-map")
    st.plotly_chart(fig_map, use_container_width=True)
else:
    st.warning("No valid lat/lon data found for map")
