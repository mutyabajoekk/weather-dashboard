import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
from datetime import datetime

current_year = datetime.now().year
previous_year = current_year - 1
current_year = 2026


st.set_page_config(page_title="Uganda Weather Dashboard", layout="wide")
st.title("🌦️ Uganda Rainfall & Temperature Dashboard")

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
#rainfall
show_rain_ltm = st.sidebar.checkbox("Show Rainfall LTM (1991–2020)", value=True)
show_rain_prev = st.sidebar.checkbox(
    f"Show Rainfall {previous_year}", value=True
)
show_rain_curr = st.sidebar.checkbox(
    f"Show Rainfall {current_year}", value=True
)

show_rain_anomalies = st.sidebar.checkbox("Show Rainfall Anomalies", value=False)

#temperature
show_temp_ltm = st.sidebar.checkbox("Show Temp LTM (2002–2020)", value=True)
show_temp_prev = st.sidebar.checkbox(
    f"Show Temp {previous_year}", value=True
)
show_temp_curr = st.sidebar.checkbox(
    f"Show Temp {current_year}", value=True
)
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
rain_ltm = (
    rain_filt[(rain_filt['year'] >= 1991) & (rain_filt['year'] <= 2020)]
    .groupby('month')['rainfall_mm']
    .mean()
    .reindex(months)
)

rain_prev = (
    rain_filt[rain_filt['year'] == previous_year]
    .groupby('month')['rainfall_mm']
    .mean()
    .reindex(months)
)

rain_curr = (
    rain_filt[rain_filt['year'] == current_year]
    .groupby('month')['rainfall_mm']
    .mean()
    .reindex(months)
)

rain_anom_prev = rain_prev - rain_ltm
rain_anom_curr = rain_curr - rain_ltm



# Temperature aggregates
temp_ltm = (
    temp_filt[(temp_filt['year'] >= 2002) & (temp_filt['year'] <= 2020)]
    .groupby('month')['temperature']
    .mean()
    .reindex(months)
)

temp_prev = (
    temp_filt[temp_filt['year'] == previous_year]
    .groupby('month')['temperature']
    .mean()
    .reindex(months)
)

temp_curr = (
    temp_filt[temp_filt['year'] == current_year]
    .groupby('month')['temperature']
    .mean()
    .reindex(months)
)

# Temperature aggregates (NO smoothing – behaves like rainfall)
temp_ltm_plot  = temp_ltm
temp_prev_plot = temp_prev
temp_curr_plot = temp_curr

# Anomalies
temp_anom_prev = temp_prev_s - temp_ltm_s
temp_anom_curr = temp_curr_s - temp_ltm_s


# Charts
col1, col2 = st.columns(2)

with col1:
    st.subheader(f"🌧️ Rainfall in {selected_subcounty if selected_subcounty != '(All)' else selected_district}")
    fig = go.Figure()

    if show_rain_ltm:
        fig.add_bar(
            x=month_labels,
            y=rain_ltm,
            name='LTM (1991–2020)',
            marker_color='royalblue'
        )

    if show_rain_prev:
        fig.add_bar(
            x=month_labels,
            y=rain_prev,
            name=str(previous_year),
            marker_color='gray'
        )

    if show_rain_curr:
        fig.add_bar(
            x=month_labels,
            y=rain_curr,
            name=str(current_year),
            marker_color='orangered'
        )

    if show_rain_anomalies:
        fig.add_scatter(
            x=month_labels,
            y=rain_anom_prev,
            name=f'{previous_year} Anomaly',
            mode='lines+markers'
        )
        fig.add_scatter(
            x=month_labels,
            y=rain_anom_curr,
            name=f'{current_year} Anomaly',
            mode='lines+markers'
        )

    fig.update_layout(
        yaxis_title='Rainfall (mm)',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation='h', y=-0.2)
    )

    st.plotly_chart(fig, use_container_width=True)

    rain_csv = pd.DataFrame({
    'Month': month_labels,
    'LTM (1991–2020)': rain_ltm.values,
    str(previous_year): rain_prev.values,
    str(current_year): rain_curr.values
    }).to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download rainfall data as CSV", data=rain_csv,
                       file_name=f"rainfall_{selected_district}_{selected_subcounty}.csv", mime='text/csv')
#plotting temperature
with col2:
    st.subheader(f"🌡️ Temperature in {selected_subcounty if selected_subcounty != '(All)' else selected_district}")
    fig2 = go.Figure()

    if show_temp_ltm:
		fig2.add_scatter(
			x=month_labels,
			y=temp_ltm_plot,
			name='LTM (2002–2020)',
			mode='lines+markers',
			line=dict(color='royalblue')
    )

	if show_temp_prev:
		fig2.add_scatter(
			x=month_labels,
			y=temp_prev_plot,
			name=str(previous_year),
			mode='lines+markers',
			line=dict(color='gray')
    )

	if show_temp_curr:
		fig2.add_scatter(
			x=month_labels,
			y=temp_curr_plot,
			name=str(current_year),
			mode='lines+markers',
			line=dict(color='orangered')
    )


    if show_temp_anomalies:
        fig2.add_scatter(
            x=month_labels,
            y=temp_anom_prev,
            name=f'{previous_year} Anomaly',
            mode='lines+markers'
        )
        fig2.add_scatter(
            x=month_labels,
            y=temp_anom_curr,
            name=f'{current_year} Anomaly',
            mode='lines+markers'
        )

    fig2.update_layout(
        yaxis_title='Temperature (°C)',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation='h', y=-0.2)
    )

    st.plotly_chart(fig2, use_container_width=True)

# exporting temperature to csv
    temp_csv = pd.DataFrame({
    'Month': month_labels,
    'LTM (2002–2020)': temp_ltm_s.values,
    str(previous_year): temp_prev_s.values,
    str(current_year): temp_curr_s.values
}).to_csv(index=False).encode('utf-8')

st.download_button(
    "📥 Download temperature data as CSV",
    data=temp_csv,
    file_name=f"temperature_{selected_district}_{selected_subcounty}.csv",
    mime='text/csv'
)


# Data sources
st.markdown("---")
st.markdown(
    "📡 **Data Sources:**\n\n"
    "- 🌧️ **Rainfall** data is derived from the **Climate Hazards Group InfraRed Precipitation with Station data (CHIRPS) from 1981 to date**.\n"
    "- 🌡️ **Temperature** data comes from the **ERA5** as hosted on the ESA Climate center"
	"		
)

# Last updated
st.markdown(f"_Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_")

# open terminal use:   streamlit run rain_temp_streamlit_app.py     in the folder where the csvs are


# site is on https://weather-dashboard-fr7drp3vvadjyxe4qwdzzt.streamlit.app/

