# Interactive Weather Dashboard

A Python-based interactive weather dashboard that auto-detects your location and visualizes real-time weather data using **Plotly** and the free [Open-Meteo](https://open-meteo.com/) API.

## Features
- Auto-detects your region via IP geolocation
- Fetches 30-day historical data + 7-day forecast
- Interactive multi-panel chart:
  - Temperature (min / mean / max band)
  - Precipitation
  - Wind speed
  - Relative humidity
- Range selector buttons (7d / 2w / 1m / All)
- Dark theme, unified hover tooltips

## Requirements
```
pip install requests plotly pandas
```

## Run
```
python weather_dashboard.py
```

The chart opens as a local HTML file in your default browser — no server required.
