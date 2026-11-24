# Weather-Aware Truck Routing

Full-stack weather-aware truck routing application built with a **Django** backend and a **React (Vite) + Leaflet** frontend.

## Key Features
- **Multi-Route Discovery:** Fetches up to 3 driving routes via OpenRouteService (HGV) with OSRM fallback and Nominatim geocoding.
- **ETA & Checkpoint Sampling:** Samples route checkpoints at **10, 25, or 50 mile** intervals and calculates estimated arrival times (ETA).
- **Weather & Load-Adjusted Risk Engine:** Queries Open-Meteo hourly forecasts (`mph` wind speed, `in/hr` rain and snow) and evaluates risk tiers (`Low`, `Moderate`, `High`, `Severe`, `No Travel`) accounting for truck load weight (`lb`).
- **4-Step Route Recommendation:** Ranks routes by fewest `Severe` miles, fewest `High` miles, lowest average risk score, and shortest travel time.
- **Interactive Map & 0–48h Forecast Slider:** Visualizes routes, checkpoint popups, checkpoint weather/risk tables, and a `0–48h` forecast shift corridor heatmap.

## Local Setup

### Backend (Django)
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
# Create backend/.env with ORS_API_KEY=... and DEBUG=True
python manage.py runserver