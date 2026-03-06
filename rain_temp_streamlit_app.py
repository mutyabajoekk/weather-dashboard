import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
from datetime import datetime

# ------------------------------------------------------------------
# Year logic
# ------------------------------------------------------------------
current_year = 2026
previous_year = current_year - 1

# ------------------------------------------------------------------
# Streamlit config
# ------------------------------------------------------------------
st.set_page_config(page_title="Uganda Weather Dashboard", layout="wide")
st.title("🌦️ Uganda Rainfall & Temperature Dashboard")

# ------------------------------------------------------------------
# Data loaders
# ------------------------------------------------------------------
@st.cache_data
def load_rainfall_data():
    df = pd.read_csv("cleaned_rainfall.csv")
    df.columns = df.columns.str.lower().str.strip()
    df.rename(
        columns={"dname2024": "district", "scname2024": "subcounty"},
        inplace=True
    )
    df["date"] = pd.to_datetime(df["date"])
    return df


@st.cache_data
def load_temperature_data():
    df = pd.read_csv("temp_data.csv")
    df.columns = df.columns.str.lower().str.strip()
    df["date"] = pd.to_datetime(df["date"])
    return df


rain_df = load_rainfall_data()
temp_df = load_temperature_data()

# ------------------------------------------------------------------
# Visitor counter
# ------------------------------------------------------------------
count_file = "visitor_count.txt"
if not os.path.exists(count_file):
    with open(count_file, "w") as f:
        f.write("0")

with open(count_file, "r+") as f:
    count = int(f.read().strip()) + 1
    f.seek(0)
    f.write(str(count))

st.sidebar.markdown(f"👥 Visitors: **{count}**")

# ------------------------------------------------------------------
# Selectors
# ------------------------------------------------------------------
districts = sorted(
    set(rain_df["district"].dropna()) |
    set(temp_df["district"].dropna())
)
selected_district = st.sidebar.selectbox("Select District", districts)

subcounties = sorted(
    set(rain_df[rain_df["district"] == selected_district]["subcounty"].dropna()) |
    set(temp_df[temp_df["district"] == selected_district]["subcounty"].dropna())
)
selected_subcounty = st.sidebar.selectbox(
    "Select Subcounty (optional)",
    ["(All)"] + subcounties
)

# ------------------------------------------------------------------
# Sidebar options
# ------------------------------------------------------------------
show_rain_ltm = st.sidebar.checkbox("Show Rainfall LTM (1991–2020)", True)
show_rain_prev = st.sidebar.checkbox(f"Show Rainfall {previous_year}", True)
show_rain_curr = st.sidebar.checkbox(f"Show Rainfall {current_year}", True)
show_rain_anomalies = st.sidebar.checkbox("Show Rainfall Anomalies", False)

show_temp_ltm = st.sidebar.checkbox("Show Temp LTM (2002–2020)", True)
show_temp_prev = st.sidebar.checkbox(f"Show Temp {previous_year}", True)
show_temp_curr = st.sidebar.checkbox(f"Show Temp {current_year}", True)
show_temp_anomalies = st.sidebar.checkbox("Show Temp Anomalies", False)

# ------------------------------------------------------------------
# Time helpers
# ------------------------------------------------------------------
months = range(1, 13)
month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# ------------------------------------------------------------------
# Filter data
# ------------------------------------------------------------------
rain_filt = rain_df[rain_df["district"] == selected_district]
temp_filt = temp_df[temp_df["district"] == selected_district]

if selected_subcounty != "(All)":
    rain_filt = rain_filt[rain_filt["subcounty"] == selected_subcounty]
    temp_filt = temp_filt[temp_filt["subcounty"] == selected_subcounty]

for df in (rain_filt, temp_filt):
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month

# ------------------------------------------------------------------
# Rainfall aggregates
# ------------------------------------------------------------------
rain_ltm = (
    rain_filt[(rain_filt["year"] >= 1991) & (rain_filt["year"] <= 2020)]
    .groupby("month")["rainfall_mm"]
    .mean()
    .reindex(months)
)

rain_prev = (
    rain_filt[rain_filt["year"] == previous_year]
    .groupby("month")["rainfall_mm"]
    .mean()
    .reindex(months)
)

rain_curr = (
    rain_filt[rain_filt["year"] == current_year]
    .groupby("month")["rainfall_mm"]
    .mean()
    .reindex(months)
)

rain_anom_prev = rain_prev - rain_ltm
rain_anom_curr = rain_curr - rain_ltm

# ------------------------------------------------------------------
# Rainfall download dataframe
# ------------------------------------------------------------------
rain_download = pd.DataFrame({
    "Month": month_labels,
    "Rainfall_LTM_1991_2020_mm": rain_ltm.values,
    f"Rainfall_{previous_year}_mm": rain_prev.values,
    f"Rainfall_{current_year}_mm": rain_curr.values,
    f"Anomaly_{previous_year}_mm": rain_anom_prev.values,
    f"Anomaly_{current_year}_mm": rain_anom_curr.values
})

# ------------------------------------------------------------------
# Temperature aggregates (MATCH RAINFALL BEHAVIOUR)
# ------------------------------------------------------------------
temp_ltm = (
    temp_filt[(temp_filt["year"] >= 1984) & (temp_filt["year"] <= 2010)]
    .groupby("month")["temperature"]
    .mean()
    .reindex(months)
)

temp_prev = (
    temp_filt[temp_filt["year"] == previous_year]
    .groupby("month")["temperature"]
    .mean()
    .reindex(months)
)

temp_curr = (
    temp_filt[temp_filt["year"] == current_year]
    .groupby("month")["temperature"]
    .mean()
    .reindex(months)
)

temp_anom_prev = temp_prev - temp_ltm
temp_anom_curr = temp_curr - temp_ltm

# ------------------------------------------------------------------
# Temperature download dataframe
# ------------------------------------------------------------------
temp_download = pd.DataFrame({
    "Month": month_labels,
    "Temp_LTM_1984_2010_C": temp_ltm.values,
    f"Temp_{previous_year}_C": temp_prev.values,
    f"Temp_{current_year}_C": temp_curr.values,
    f"Anomaly_{previous_year}_C": temp_anom_prev.values,
    f"Anomaly_{current_year}_C": temp_anom_curr.values
})

# ------------------------------------------------------------------
# Charts
# ------------------------------------------------------------------
col1, col2 = st.columns(2)

# ===================== Rainfall =====================
with col1:
    st.subheader(
        f"🌧️ Rainfall in "
        f"{selected_subcounty if selected_subcounty != '(All)' else selected_district}"
    )

    fig = go.Figure()

    if show_rain_ltm:
        fig.add_bar(x=month_labels, y=rain_ltm, name="LTM (1991–2020)")

    if show_rain_prev:
        fig.add_bar(x=month_labels, y=rain_prev, name=str(previous_year))

    if show_rain_curr:
        fig.add_bar(x=month_labels, y=rain_curr, name=str(current_year))

    if show_rain_anomalies:
        fig.add_scatter(
            x=month_labels, y=rain_anom_prev,
            name=f"{previous_year} Anomaly",
            mode="lines+markers"
        )
        fig.add_scatter(
            x=month_labels, y=rain_anom_curr,
            name=f"{current_year} Anomaly",
            mode="lines+markers"
        )

    fig.update_layout(
        yaxis_title="Rainfall (mm)",
        legend=dict(orientation="h", y=-0.2)
    )

    st.plotly_chart(fig, use_container_width=True)
     # DOWNLOAD BUTTON (INSIDE col1)
    csv_rain = rain_download.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="⬇️ Download Rainfall Data (CSV)",
        data=csv_rain,
        file_name=f"{selected_district}_rainfall_data.csv",
        mime="text/csv"
    )

# ===================== Temperature =====================
with col2:
    st.subheader(
        f"🌡️ Temperature in "
        f"{selected_subcounty if selected_subcounty != '(All)' else selected_district}"
    )

    fig2 = go.Figure()

    if show_temp_ltm:
        fig2.add_scatter(
            x=month_labels,
            y=temp_ltm,
            name="LTM (1980–2010)",
            mode="lines+markers"
        )

    if show_temp_prev:
        fig2.add_scatter(
            x=month_labels,
            y=temp_prev,
            name=str(previous_year),
            mode="lines+markers"
        )

    if show_temp_curr:
        fig2.add_scatter(
            x=month_labels,
            y=temp_curr,
            name=str(current_year),
            mode="lines+markers"
        )

    if show_temp_anomalies:
        fig2.add_scatter(
            x=month_labels,
            y=temp_anom_prev,
            name=f"{previous_year} Anomaly",
            mode="lines+markers"
        )
        fig2.add_scatter(
            x=month_labels,
            y=temp_anom_curr,
            name=f"{current_year} Anomaly",
            mode="lines+markers"
        )

    fig2.update_layout(
        yaxis_title="Temperature (°C)",
        legend=dict(orientation="h", y=-0.2)
    )

    st.plotly_chart(fig2, use_container_width=True)
    
     # DOWNLOAD BUTTON (INSIDE col2)
    csv_temp = temp_download.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="⬇️ Download Temperature Data (CSV)",
        data=csv_temp,
        file_name=f"{selected_district}_temperature_data.csv",
        mime="text/csv"
    )


# ------------------------------------------------------------------
# Data sources & footer
# ------------------------------------------------------------------
st.markdown("---")
st.markdown(
    "📡 **Data Sources:**\n\n"
    "- 🌧️ Rainfall: CHIRPS (1981–present)\n"
    "- 🌡️ Temperature: ERA5 (ESA Climate Data Centre)"
)

st.markdown(
    f"_Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"
)
