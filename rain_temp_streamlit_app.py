import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
from datetime import datetime

st.set_page_config(page_title="Weather Dashboard", layout="wide")
st.title("🌦️ Rainfall & Temperature Dashboard")

@st.cache_data
def load_rainfall_data():
    df = pd.read_csv("cleaned_rainfall.csv")
    df.columns = df.columns.str.lower().str.strip()
    df.rename(columns={'dname2024': 'district', 'scname2024': 'subcounty'}, inplace=True)
    df['date'] = pd.to_datetime(df['date'])
    return df

@st.cache_data
def load_temperature_data():
    df = pd.read_csv("temp_data.csv")
    df.columns = df.columns.str.lower().str.strip()
    df['date'] = pd.to_datetime(df['date'])
    return df

rain_df = load_rainfall_data()
temp_df = load_temperature_data()

# Visitors counter
count_file = "visitor_count.txt"
if not os.path.exists(count_file):
    with open(count_file, 'w') as f:
        f.write("0")
with open(count_file, 'r+') as f:
    count = int(f.read().strip()) + 1
    f.seek(0)
    f.write(str(count))
st.sidebar.markdown(f"👥 Visitors: **{count}**")

# District and subcounty selectors
districts = sorted(set(rain_df['district'].dropna()) | set(temp_df['district'].dropna()))
selected_district = st.sidebar.selectbox("Select District", districts)

subcounties = sorted(set(rain_df[rain_df['district']==selected_district]['subcounty'].dropna()) |
                     set(temp_df[temp_df['district']==selected_district]['subcounty'].dropna()))
selected_subcounty = st.sidebar.selectbox("Select Subcounty (optional)", ["(All)"] + subcounties)

# Options
show_rain_ltm = st.sidebar.checkbox("Show Rainfall LTM (1991–2020)", value=True)
show_rain_2024 = st.sidebar.checkbox("Show Rainfall 2024", value=True)
show_rain_2025 = st.sidebar.checkbox("Show Rainfall 2025", value=True)
show_rain_anomalies = st.sidebar.checkbox("Show Rainfall Anomalies", value=False)

show_temp_ltm = st.sidebar.checkbox("Show Temp LTM (2002–2020)", value=True)
show_temp_2024 = st.sidebar.checkbox("Show Temp 2024", value=True)
show_temp_2025 = st.sidebar.checkbox("Show Temp 2025", value=True)
show_temp_anomalies = st.sidebar.checkbox("Show Temp Anomalies", value=False)

months = range(1,13)
month_labels = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

# Filter data
rain_filt = rain_df[rain_df['district']==selected_district]
temp_filt = temp_df[temp_df['district']==selected_district]
if selected_subcounty != "(All)":
    rain_filt = rain_filt[rain_filt['subcounty']==selected_subcounty]
    temp_filt = temp_filt[temp_filt['subcounty']==selected_subcounty]

rain_filt['year'] = rain_filt['date'].dt.year
rain_filt['month'] = rain_filt['date'].dt.month
temp_filt['year'] = temp_filt['date'].dt.year
temp_filt['month'] = temp_filt['date'].dt.month

# Rainfall aggregates
rain_ltm = rain_filt[(rain_filt['year']>=1991)&(rain_filt['year']<=2020)].groupby('month')['rainfall_mm'].mean().reindex(months)
rain_2024 = rain_filt[rain_filt['year']==2024].groupby('month')['rainfall_mm'].mean().reindex(months)
rain_2025 = rain_filt[rain_filt['year']==2025].groupby('month')['rainfall_mm'].mean().reindex(months)

rain_ltm_s = rain_ltm
rain_2024_s = rain_2024
rain_2025_s = rain_2025

rain_anom_2024 = rain_2024 - rain_ltm
rain_anom_2025 = rain_2025 - rain_ltm


# Temperature aggregates
temp_ltm = temp_filt[(temp_filt['year']>=2002)&(temp_filt['year']<=2020)].groupby('month')['temperature'].mean().reindex(months)
temp_2024 = temp_filt[temp_filt['year']==2024].groupby('month')['temperature'].mean().reindex(months)
temp_2025 = temp_filt[temp_filt['year']==2025].groupby('month')['temperature'].mean().reindex(months)

temp_ltm_s = temp_ltm.rolling(window=3, center=True, min_periods=1).mean()
temp_2024_s = temp_2024.rolling(window=3, center=True, min_periods=1).mean()
temp_2025_s = temp_2025.rolling(window=3, center=True, min_periods=1).mean()

temp_anom_2024 = temp_2024_s - temp_ltm_s
temp_anom_2025 = temp_2025_s - temp_ltm_s

# Charts
col1, col2 = st.columns(2)

with col1:
    st.subheader(f"🌧️ Rainfall in {selected_subcounty if selected_subcounty != '(All)' else selected_district}")
    fig = go.Figure()
    if show_rain_ltm:
        fig.add_bar(x=month_labels, y=rain_ltm_s, name='LTM (1991–2020)', marker_color='royalblue',
                    hovertemplate='Month: %{x}<br>Rainfall: %{y:.0f} mm')
    if show_rain_2024:
        fig.add_bar(x=month_labels, y=rain_2024_s, name='2024', marker_color='gray',
                    hovertemplate='Month: %{x}<br>Rainfall: %{y:.0f} mm')
    if show_rain_2025:
        fig.add_bar(x=month_labels, y=rain_2025_s, name='2025', marker_color='orangered',
                    hovertemplate='Month: %{x}<br>Rainfall: %{y:.0f} mm')
    if show_rain_anomalies:
        fig.add_scatter(x=month_labels, y=rain_anom_2024, name='2024 Anomaly', mode='lines+markers',
                        line=dict(color='purple'), hovertemplate='Month: %{x}<br>Anomaly: %{y:.0f} mm')
        fig.add_scatter(x=month_labels, y=rain_anom_2025, name='2025 Anomaly', mode='lines+markers',
                        line=dict(color='green'), hovertemplate='Month: %{x}<br>Anomaly: %{y:.0f} mm')
    fig.update_layout(yaxis_title='Rainfall (mm)', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                      font=dict(color='black'), legend=dict(orientation='h', y=-0.2))
    st.plotly_chart(fig, use_container_width=True)

    rain_csv = pd.DataFrame({
        'Month': month_labels,
        'LTM (1991–2020)': rain_ltm_s.values,
        '2024': rain_2024_s.values,
        '2025': rain_2025_s.values
    }).to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download rainfall data as CSV", data=rain_csv,
                       file_name=f"rainfall_{selected_district}_{selected_subcounty}.csv", mime='text/csv')

with col2:
    st.subheader(f"🌡️ Temperature in {selected_subcounty if selected_subcounty != '(All)' else selected_district}")
    fig2 = go.Figure()
    if show_temp_ltm:
        fig2.add_scatter(x=month_labels, y=temp_ltm_s, name='LTM (2002–2020)', mode='lines+markers',
                         line=dict(color='royalblue'), hovertemplate='Month: %{x}<br>Temp: %{y:.1f} °C')
    if show_temp_2024:
        fig2.add_scatter(x=month_labels, y=temp_2024_s, name='2024', mode='lines+markers',
                         line=dict(color='gray'), hovertemplate='Month: %{x}<br>Temp: %{y:.1f} °C')
    if show_temp_2025:
        fig2.add_scatter(x=month_labels, y=temp_2025_s, name='2025', mode='lines+markers',
                         line=dict(color='orangered'), hovertemplate='Month: %{x}<br>Temp: %{y:.1f} °C')
    if show_temp_anomalies:
        fig2.add_scatter(x=month_labels, y=temp_anom_2024, name='2024 Anomaly', mode='lines+markers',
                         line=dict(color='purple'), hovertemplate='Month: %{x}<br>Anomaly: %{y:.1f} °C')
        fig2.add_scatter(x=month_labels, y=temp_anom_2025, name='2025 Anomaly', mode='lines+markers',
                         line=dict(color='green'), hovertemplate='Month: %{x}<br>Anomaly: %{y:.1f} °C')
    fig2.update_layout(yaxis_title='Temperature (°C)', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                       font=dict(color='black'), legend=dict(orientation='h', y=-0.2))
    st.plotly_chart(fig2, use_container_width=True)

    temp_csv = pd.DataFrame({
        'Month': month_labels,
        'LTM (2002–2020)': temp_ltm_s.values,
        '2024': temp_2024_s.values,
        '2025': temp_2025_s.values
    }).to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download temperature data as CSV", data=temp_csv,
                       file_name=f"temperature_{selected_district}_{selected_subcounty}.csv", mime='text/csv')

# Data sources
st.markdown("---")
st.markdown(
    "📡 **Data Sources:**\n\n"
    "- 🌧️ **Rainfall** data is derived from the **Climate Hazards Group InfraRed Precipitation with Station data (CHIRPS) from 1981 to date**.\n"
    "- 🌡️ **Temperature** data comes from the **Moderate Resolution Imaging Spectroradiometer (MODIS)** and the **Visible Infrared Imaging Radiometer Suite (VIIRS)** satellite products."
)

# Last updated
st.markdown(f"_Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_")

# open terminal use:   streamlit run rain_temp_streamlit_app.py     in the folder where the csvs are