import streamlit as st
import pandas as pd
import plotly.express as px

# =====================================
# CONFIG
# =====================================

st.set_page_config(
    page_title="NOC KPI Monitoring Dashboard",
    layout="wide"
)

st.title("📊 NOC KPI Monitoring Dashboard")

# =====================================
# LOAD DATA
# =====================================

@st.cache_data
def load_data():
    df = pd.read_csv("kpi_data.csv")
    df.columns = df.columns.str.strip().str.lower()
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading CSV: {e}")
    st.stop()

# =====================================
# VALIDATION
# =====================================

required_cols = ["date", "site", "traffic_gb", "availability", "lat", "lon"]

for col in required_cols:
    if col not in df.columns:
        st.error(f"Missing required column: {col}")
        st.stop()

# Convert date
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date"])

# =====================================
# SIDEBAR FILTER
# =====================================

st.sidebar.header("🔎 Filter")

site_list = ["All"] + sorted(df["site"].dropna().unique())
selected_site = st.sidebar.selectbox("Site", site_list)

date_range = st.sidebar.date_input(
    "Date Range",
    [df["date"].min(), df["date"].max()]
)

# Apply filters
if selected_site != "All":
    df = df[df["site"] == selected_site]

df = df[
    (df["date"] >= pd.to_datetime(date_range[0])) &
    (df["date"] <= pd.to_datetime(date_range[1]))
]

# =====================================
# KPI SUMMARY
# =====================================

col1, col2, col3 = st.columns(3)

col1.metric("Total Sites", df["site"].nunique())
col2.metric("Avg Availability", f"{df['availability'].mean():.2f}%")
col3.metric("Total Traffic (GB)", f"{df['traffic_gb'].sum():,.0f}")

st.divider()

# =====================================
# CONGESTION DETECTION
# =====================================

st.subheader("🚨 Congestion Detection")

avail_threshold = st.slider("Availability Threshold (%)", 90, 100, 95)

df["congestion_avail"] = df["availability"] < avail_threshold

if "prb" in df.columns:
    prb_threshold = st.slider("PRB Threshold (%)", 70, 100, 85)
    df["congestion_prb"] = df["prb"] > prb_threshold
else:
    df["congestion_prb"] = False

df["congestion"] = df["congestion_avail"] | df["congestion_prb"]

congestion_df = df[df["congestion"]]

st.write("Total Congested Records:", congestion_df.shape[0])

if not congestion_df.empty:
    st.dataframe(congestion_df)
else:
    st.success("No congestion detected")

st.divider()

# =====================================
# AVAILABILITY TREND
# =====================================

st.subheader("📈 Availability Trend")

trend_df = df.groupby("date")["availability"].mean().reset_index()

fig_trend = px.line(
    trend_df,
    x="date",
    y="availability",
    markers=True
)

st.plotly_chart(fig_trend, use_container_width=True)

# =====================================
# SITE MAP
# =====================================

st.subheader("🗺 Site Location Map")

map_df = df.dropna(subset=["lat", "lon"])

if not map_df.empty:
    fig_map = px.scatter_mapbox(
        map_df,
        lat="lat",
        lon="lon",
        color="availability",
        hover_name="site",
        zoom=6,
        height=600
    )

    fig_map.update_layout(mapbox_style="open-street-map")
    st.plotly_chart(fig_map, use_container_width=True)
else:
    st.warning("No valid lat/lon data available")
