import { useState } from 'react';
import TripForm from './components/TripForm';
import RouteCards from './components/RouteCards';
import RouteMap from './components/RouteMap';
import CheckpointTable from './components/CheckpointTable';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');

export default function App() {
  const [tripData, setTripData] = useState(null);
  const [selectedRouteId, setSelectedRouteId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState('');
  const [error, setError] = useState('');

  const handlePlanTrip = async (formPayload) => {
    setLoading(true);
    setLoadingStep('Geocoding & computing 3 HGV routes...');
    setError('');

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 65000);
    const stepTimer = setTimeout(() => {
      setLoadingStep('Sampling checkpoints & evaluating ETA weather...');
    }, 3500);

    try {
      const response = await fetch(`${API_BASE_URL}/api/plan-trip/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formPayload),
        signal: controller.signal,
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || 'Failed to evaluate routes.');
      }

      setTripData(data);
      const bestRoute = data.routes.find((r) => r.is_recommended) || data.routes[0];
      setSelectedRouteId(bestRoute ? bestRoute.id : null);
    } catch (err) {
      if (err.name === 'AbortError') {
        setError('Request timed out (65s). Render free server may be waking up — please click Find Safest Route again.');
      } else {
        setError(err.message || 'Could not connect to the routing server.');
      }
    } finally {
      clearTimeout(timeoutId);
      clearTimeout(stepTimer);
      setLoading(false);
      setLoadingStep('');
    }
  };

  const selectedRoute = tripData?.routes?.find((r) => r.id === selectedRouteId) || null;
  const isSimulated = tripData?.weather_source === 'simulated';

  return (
    <div>
      <header className="app-header">
        <div>
          <h1>Spotter — Weather-Aware Truck Routing</h1>
          <p>HGV Route Safety, ETA Weather Sampling & Load-Adjusted Risk Engine</p>
        </div>
        <span className="header-badge">
          {isSimulated ? 'React + Django · Simulated Weather' : 'React + Django · Live Forecast'}
        </span>
      </header>

      <main className="container">
        <TripForm onSubmit={handlePlanTrip} loading={loading} />

        {loading && loadingStep && (
          <div className="card" style={{ padding: '12px 18px', fontWeight: 600, color: '#1e40af' }}>
            {loadingStep}
          </div>
        )}

        {error && <div className="error-banner">{error}</div>}

        {isSimulated && (
          <div
            className="card"
            style={{
              padding: '10px 16px',
              background: '#fefce8',
              borderColor: '#fde047',
              color: '#854d0e',
              fontSize: '0.9rem',
            }}
          >
            <strong>Notice:</strong> Simulated weather forecast active (live Open-Meteo API temporarily rate-limited on shared cloud IP).
          </div>
        )}

        {tripData && (
          <>
            <RouteCards
              routes={tripData.routes}
              selectedRouteId={selectedRouteId}
              onSelectRoute={setSelectedRouteId}
            />

            <RouteMap
              origin={tripData.origin}
              destination={tripData.destination}
              routes={tripData.routes}
              selectedRouteId={selectedRouteId}
              onSelectRoute={setSelectedRouteId}
            />

            <CheckpointTable route={selectedRoute} />
          </>
        )}
      </main>
    </div>
  );
}