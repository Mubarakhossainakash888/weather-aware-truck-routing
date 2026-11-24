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
  const [error, setError] = useState('');

  const handlePlanTrip = async (formPayload) => {
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE_URL}/api/plan-trip/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formPayload),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || 'Failed to evaluate routes.');
      }

      setTripData(data);
      const bestRoute = data.routes.find((r) => r.is_recommended) || data.routes[0];
      setSelectedRouteId(bestRoute ? bestRoute.id : null);
    } catch (err) {
      setError(err.message || 'Could not connect to the routing server.');
    } finally {
      setLoading(false);
    }
  };

  const selectedRoute = tripData?.routes?.find((r) => r.id === selectedRouteId) || null;

  return (
    <div>
      <header className="app-header">
        <div>
          <h1>Spotter — Weather-Aware Truck Routing</h1>
          <p>HGV Route Safety, ETA Weather Sampling & Load-Adjusted Risk Engine</p>
        </div>
        <span className="header-badge">React + Django · Live Forecast</span>
      </header>

      <main className="container">
        <TripForm onSubmit={handlePlanTrip} loading={loading} />

        {error && <div className="error-banner">{error}</div>}

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