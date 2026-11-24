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
```

### 2. Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev
```
The app runs at http://localhost:5173 and talks to the Django API at http://127.0.0.1:8000 by default. To point it at a deployed backend, set `VITE_API_BASE_URL` in `frontend/.env`.

## Deployment
- **Frontend (Vercel):** import the `frontend/` directory; set `VITE_API_BASE_URL` to the Render backend URL.
- **Backend (Render):** deploy the `backend/` directory with Gunicorn (for example `gunicorn config.wsgi` from inside `backend/`); set these environment variables — `ORS_API_KEY` (OpenRouteService key), `DJANGO_SECRET_KEY` (a long random string), `DEBUG=False`. Never commit real keys; `.env` files are git-ignored.

## How the risk engine works
Wind, rain, and snow are each classified into Low / Moderate / High / Severe / No Travel (wind ≥55 mph is always No Travel; 45–54 mph with a load over 30,000 lb is No Travel; 35–44 mph with a load over 40,000 lb is Severe). The worst of the three sets the checkpoint risk. Routes are ranked by fewest No Travel miles, then Severe miles, then High miles, then lowest average risk, then shortest travel time.

## Weather fallback
Open-Meteo is the live forecast source. If it rate-limits the request (HTTP 429), the backend retries and then falls back to clearly labelled simulated weather so the app keeps working — the UI shows a "Simulated Weather" badge and notice in that case.