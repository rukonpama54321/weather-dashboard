"""
Interactive Weather Dashboard
==============================
• Auto-detects your region via IP geolocation
• Fetches 30-day history + 7-day forecast from Open-Meteo (free, no API key)
• Renders a multi-panel interactive Plotly chart in your browser
"""

import requests
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta


# ── 1. Auto-detect location via IP ────────────────────────────────────────────
def get_location():
    try:
        r = requests.get("https://ipinfo.io/json", timeout=5)
        data = r.json()
        city    = data.get("city", "Unknown")
        region  = data.get("region", "")
        country = data.get("country", "")
        lat, lon = map(float, data.get("loc", "0,0").split(","))
        label = f"{city}, {region}, {country}".strip(", ")
        return lat, lon, label
    except Exception:
        # Fallback to New York
        return 40.7128, -74.0060, "New York, NY, US (fallback)"


lat, lon, location_name = get_location()
print(f"\n📍 Detected location : {location_name}  ({lat:.4f}, {lon:.4f})")


# ── 2. Fetch weather data from Open-Meteo ─────────────────────────────────────
today      = datetime.today()
end_date   = today.strftime("%Y-%m-%d")
start_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")

url = "https://api.open-meteo.com/v1/forecast"
params = {
    "latitude":   lat,
    "longitude":  lon,
    "daily": [
        "temperature_2m_max",
        "temperature_2m_min",
        "temperature_2m_mean",
        "precipitation_sum",
        "windspeed_10m_max",
        "relative_humidity_2m_mean",
        "weathercode",
    ],
    "timezone":     "auto",
    "past_days":    30,
    "forecast_days": 7,
}

print("⏳ Fetching weather data from Open-Meteo…")
resp = requests.get(url, params=params, timeout=15)
resp.raise_for_status()
raw = resp.json()

# ── 3. Parse into DataFrame ───────────────────────────────────────────────────
df = pd.DataFrame(raw["daily"])
df["time"] = pd.to_datetime(df["time"])

today_ts = pd.Timestamp.today().normalize()
df["period"] = df["time"].apply(
    lambda t: "Forecast" if t >= today_ts else "Historical"
)

hist = df[df["period"] == "Historical"].copy()
fore = df[df["period"] == "Forecast"].copy()

print(f"✅ {len(hist)} historical days  +  {len(fore)} forecast days loaded")

# ── 4. WMO weather-code labels ────────────────────────────────────────────────
WMO = {
    0: "Clear sky",       1: "Mainly clear",     2: "Partly cloudy",
    3: "Overcast",       45: "Fog",             48: "Icy fog",
   51: "Light drizzle",  53: "Drizzle",         55: "Heavy drizzle",
   61: "Slight rain",    63: "Moderate rain",   65: "Heavy rain",
   71: "Slight snow",    73: "Moderate snow",   75: "Heavy snow",
   80: "Rain showers",   81: "Showers",         82: "Violent showers",
   95: "Thunderstorm",   96: "T-storm + hail",  99: "Heavy t-storm",
}
df["condition"] = df["weathercode"].map(WMO).fillna("Unknown")

# ── 5. Build interactive dashboard ────────────────────────────────────────────
TITLE_COLOR = "#e0e0e0"
GRID_COLOR  = "rgba(255,255,255,0.07)"

fig = make_subplots(
    rows=4, cols=1,
    shared_xaxes=True,
    subplot_titles=(
        "🌡  Temperature (°C)",
        "🌧  Precipitation (mm)",
        "💨  Max Wind Speed (km/h)",
        "💧  Relative Humidity (%)",
    ),
    vertical_spacing=0.065,
    row_heights=[0.32, 0.22, 0.22, 0.22],
)

# helper: add a vertical shaded region for the forecast window
def add_forecast_shade(fig):
    if len(fore) == 0:
        return
    fig.add_vrect(
        x0=fore["time"].iloc[0],
        x1=fore["time"].iloc[-1],
        fillcolor="rgba(255,220,50,0.06)",
        line_width=0.5,
        line_color="rgba(255,220,50,0.3)",
        annotation_text=" Forecast",
        annotation_position="top left",
        annotation_font=dict(color="gold", size=11),
    )

add_forecast_shade(fig)

# ── Row 1 : Temperature ───────────────────────────────────────────────────────
# Historical band (min → max filled)
fig.add_trace(go.Scatter(
    x=hist["time"], y=hist["temperature_2m_max"],
    name="Max Temp",
    mode="lines",
    line=dict(color="tomato", width=1.8),
    legendgroup="temp",
), row=1, col=1)

fig.add_trace(go.Scatter(
    x=hist["time"], y=hist["temperature_2m_min"],
    name="Min Temp",
    mode="lines",
    line=dict(color="steelblue", width=1.8),
    fill="tonexty",
    fillcolor="rgba(100,149,237,0.14)",
    legendgroup="temp",
), row=1, col=1)

fig.add_trace(go.Scatter(
    x=hist["time"], y=hist["temperature_2m_mean"],
    name="Mean Temp",
    mode="lines+markers",
    line=dict(color="gold", width=1.5),
    marker=dict(size=4, color="gold"),
    legendgroup="temp",
), row=1, col=1)

# Forecast temperature
fig.add_trace(go.Scatter(
    x=fore["time"], y=fore["temperature_2m_max"],
    name="Max (Forecast)",
    mode="lines",
    line=dict(color="tomato", width=1.8, dash="dash"),
    legendgroup="temp_f",
    showlegend=True,
), row=1, col=1)

fig.add_trace(go.Scatter(
    x=fore["time"], y=fore["temperature_2m_min"],
    name="Min (Forecast)",
    mode="lines",
    line=dict(color="steelblue", width=1.8, dash="dash"),
    fill="tonexty",
    fillcolor="rgba(100,149,237,0.08)",
    legendgroup="temp_f",
    showlegend=True,
), row=1, col=1)

# ── Row 2 : Precipitation ─────────────────────────────────────────────────────
fig.add_trace(go.Bar(
    x=hist["time"], y=hist["precipitation_sum"],
    name="Precip (Historical)",
    marker_color="cornflowerblue",
    opacity=0.80,
), row=2, col=1)

fig.add_trace(go.Bar(
    x=fore["time"], y=fore["precipitation_sum"],
    name="Precip (Forecast)",
    marker_color="royalblue",
    opacity=0.55,
    marker_pattern_shape="/",
), row=2, col=1)

# ── Row 3 : Wind speed ────────────────────────────────────────────────────────
fig.add_trace(go.Scatter(
    x=hist["time"], y=hist["windspeed_10m_max"],
    name="Wind Speed",
    mode="lines",
    line=dict(color="#2ecc71", width=1.8),
    fill="tozeroy",
    fillcolor="rgba(46,204,113,0.10)",
), row=3, col=1)

fig.add_trace(go.Scatter(
    x=fore["time"], y=fore["windspeed_10m_max"],
    name="Wind (Forecast)",
    mode="lines",
    line=dict(color="#2ecc71", dash="dash", width=1.8),
), row=3, col=1)

# ── Row 4 : Humidity ──────────────────────────────────────────────────────────
fig.add_trace(go.Scatter(
    x=hist["time"], y=hist["relative_humidity_2m_mean"],
    name="Humidity",
    mode="lines",
    line=dict(color="mediumpurple", width=1.8),
    fill="tozeroy",
    fillcolor="rgba(147,112,219,0.13)",
), row=4, col=1)

fig.add_trace(go.Scatter(
    x=fore["time"], y=fore["relative_humidity_2m_mean"],
    name="Humidity (Forecast)",
    mode="lines",
    line=dict(color="mediumpurple", dash="dash", width=1.8),
), row=4, col=1)

# Clip humidity axis 0-100
fig.update_yaxes(range=[0, 100], row=4, col=1)

# ── Layout ────────────────────────────────────────────────────────────────────
fig.update_layout(
    title=dict(
        text=(
            f"<b>Interactive Weather Dashboard</b>"
            f"<br><sup>{location_name} · 30-day history + 7-day forecast"
            f" · Source: Open-Meteo.com</sup>"
        ),
        x=0.5,
        font=dict(size=18, color=TITLE_COLOR),
    ),
    height=980,
    template="plotly_dark",
    hovermode="x unified",
    legend=dict(
        orientation="v",
        yanchor="middle",
        y=0.5,
        xanchor="left",
        x=1.02,
        bgcolor="rgba(0,0,0,0.5)",
        bordercolor="rgba(255,255,255,0.15)",
        borderwidth=1,
        font=dict(size=11),
    ),
    margin=dict(t=110, b=50, l=60, r=180),
    bargap=0.18,
    paper_bgcolor="#0f0f1a",
    plot_bgcolor="#111122",
)

for axis in ["xaxis", "xaxis2", "xaxis3", "xaxis4",
             "yaxis", "yaxis2", "yaxis3", "yaxis4"]:
    fig.layout[axis].update(
        showgrid=True,
        gridcolor=GRID_COLOR,
        gridwidth=1,
    )

# Nicer subplot title colors
for ann in fig.layout.annotations:
    ann.font.color = TITLE_COLOR
    ann.font.size  = 13

# ── 6. Range-selector buttons on top x-axis ───────────────────────────────────
fig.update_xaxes(
    rangeslider=dict(visible=False),
    rangeselector=dict(
        bgcolor="rgba(255,255,255,0.07)",
        activecolor="rgba(255,220,50,0.35)",
        buttons=[
            dict(count=7,  label="7d",  step="day",  stepmode="backward"),
            dict(count=14, label="2w",  step="day",  stepmode="backward"),
            dict(count=1,  label="1m",  step="month", stepmode="backward"),
            dict(step="all", label="All"),
        ],
    ),
    row=1, col=1,
)

import os, webbrowser, tempfile

html_path = os.path.join(tempfile.gettempdir(), "weather_dashboard.html")
fig.write_html(html_path, auto_open=False)
print(f"🚀 Opening chart in your browser…  ({html_path})\n")
webbrowser.open(f"file:///{html_path}")
