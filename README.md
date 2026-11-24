# Spotter — Weather-Aware Truck Routing

Full-stack Heavy Goods Vehicle (HGV) route safety and weather risk engine built with **Django** and **React (Vite + Leaflet)**. Evaluates up to three driving corridors using ETA-aligned weather forecasts, vehicle load weight thresholds, and an interactive 0–48 hour corridor heatmap slider.

## Live Deployment
- **Frontend (Vercel):** https://weather-aware-truck-routing-eta-eight.vercel.app/
- **Backend API (Render):** https://weather-aware-truck-routing-q5od.onrender.com

## Key Features
- **HGV Multi-Route Comparison:** Fetches up to 3 routes via OpenRouteService (`driving-hgv` profile) with OSRM fallback and ranks them by safety (`No Travel` miles, `Severe` miles, `High` miles, average risk score, and travel duration).
- **ETA-Aligned Weather Sampling:** Samples checkpoints every 10, 25, or 50 miles along each route and queries hourly wind speed, rain, and snowfall aligned to the truck's exact arrival timestamp.
- **Load-Adjusted Risk Engine:** Evaluates `Low`, `Moderate`, `High`, `Severe`, and `No Travel` tiers accounting for heavy cargo weight (>30,000 lb and >40,000 lb crosswind/precipitation sensitivity rules).
- **Interactive Corridor Map & 0–48h Forecast Slider:** Displays route polylines, checkpoint risk popups, and a live 48-hour forecast shift slider.

## Local Setup

### 1. Backend (Django)
```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate | macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add your OpenRouteService API key inside backend/.env
python manage.py runserver