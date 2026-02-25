import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# =============================
# THEME
# =============================
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

def toggle_theme():
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"

st.button("TOGGLE THEME", on_click=toggle_theme)
template_style = "plotly_dark" if st.session_state.theme == "dark" else "plotly"

st.title("📊 NOC KPI Dashboard | Congestion Engine")

# =============================
# FILE UPLOAD
# =============================
file = st.file_uploader("Upload KPI CSV", type=["csv"])

if file:

    df = pd.read_csv(file)

    # CLEAN HEADER
    df.columns = df.columns.str.strip()

    # RENAME
    df = df.rename(columns={
        "Date": "date",
        "eNodeBName": "site",
        "Sector": "sector",
        "Band": "band",
        "Payload": "payload",
        "PRB": "prb",
        "Availability": "availability",
        "Lat": "lat",
        "Lon": "lon"
    })

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    st.success(f"{len(df)} rows loaded")

    # =============================
    # SIDEBAR CONTROL
    # =============================
    st.sidebar.header("FILTER CONTROL")

    site = st.sidebar.selectbox("Site", ["All"] + sorted(df["site"].unique()))
    sector = st.sidebar.selectbox("Sector", ["All"] + sorted(df["sector"].unique()))
    band = st.sidebar.selectbox("Band", ["All"] + sorted(df["band"].unique()))

    threshold = st.sidebar.slider("PRB Congestion Threshold", 70, 100, 85)
    consecutive_days_required = st.sidebar.slider("Min Consecutive Days", 1, 7, 3)

    start_date = st.sidebar.date_input("Start Date", df["date"].min())
    end_date = st.sidebar.date_input("End Date", df["date"].max())

    # APPLY FILTER
    if site != "All":
        df = df[df["site"] == site]

    if sector != "All":
        df = df[df["sector"] == sector]

    if band != "All":
        df = df[df["band"] == band]

    df = df[(df["date"] >= pd.to_datetime(start_date)) &
            (df["date"] <= pd.to_datetime(end_date))]

    # =============================
    # CONGESTION CLASSIFICATION
    # =============================
    def classify(prb):
        if prb >= threshold:
            return "Congested"
        elif prb >= threshold - 15:
            return "Warning"
        else:
            return "Normal"

    df["status"] = df["prb"].apply(classify)

    # =============================
    # CONSECUTIVE DAY DETECTION
    # =============================
    df["congested_flag"] = df["prb"] >= threshold

    df["consecutive"] = (
        df.groupby(["site", "sector"])["congested_flag"]
        .transform(lambda x: x * (x.groupby((~x).cumsum()).cumcount() + 1))
    )

    major_alarm = df[df["consecutive"] >= consecutive_days_required]

    # =============================
    # TABS
    # =============================
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 KPI Trend",
        "🚨 Congestion Monitor",
        "🏆 Top Congested Sector",
        "🗺 Geo View"
    ])

    # =============================
    # TAB 1 KPI TREND
    # =============================
    with tab1:

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df["date"],
            y=df["prb"],
            mode="lines+markers",
            name="PRB"
        ))

        fig.add_hline(y=threshold, line_dash="dash", line_color="red")

        fig.update_layout(
            template=template_style,
            height=400,
            title="PRB Trend"
        )

        st.plotly_chart(fig, use_container_width=True)

    # =============================
    # TAB 2 CONGESTION MONITOR
    # =============================
    with tab2:

        st.subheader("Congestion Records")

        if len(major_alarm) > 0:
            st.error(f"🔥 Major Congestion Detected ({len(major_alarm)} records)")
            st.dataframe(major_alarm.sort_values("prb", ascending=False))
        else:
            st.success("✅ No Major Congestion Based on Consecutive Rule")

        warning = df[df["status"] == "Warning"]
        st.subheader("Warning Level")
        st.dataframe(warning)

    # =============================
    # TAB 3 RANKING
    # =============================
    with tab3:

        ranking = (
            df[df["prb"] >= threshold]
            .groupby(["site", "sector"])
            .size()
            .reset_index(name="congestion_days")
            .sort_values("congestion_days", ascending=False)
        )

        if len(ranking) > 0:
            st.subheader("Top Congested Sector")
            st.dataframe(ranking)

            fig_rank = go.Figure()

            fig_rank.add_trace(go.Bar(
                x=ranking["congestion_days"],
                y=ranking["site"] + "_S" + ranking["sector"].astype(str),
                orientation="h"
            ))

            fig_rank.update_layout(
                template=template_style,
                height=500,
                title="Congestion Ranking"
            )

            st.plotly_chart(fig_rank, use_container_width=True)
        else:
            st.success("No congestion ranking available")

    # =============================
    # TAB 4 MAP
    # =============================
    with tab4:

        if "lat" in df.columns and "lon" in df.columns:
            map_df = df[df["prb"] >= threshold]
            st.map(map_df[["lat", "lon"]])
        else:
            st.info("Lat/Lon not detected")

    # =============================
    # AI RECOMMENDATION ENGINE
    # =============================
    st.divider()
    st.subheader("🤖 Auto Recommendation")

    if len(major_alarm) > 0:
        st.warning("""
        Recommendation:
        - Check sector capacity
        - Consider carrier expansion
        - Evaluate load balancing
        - Review peak hour traffic
        """)
    else:
        st.success("Network condition stable based on selected threshold")