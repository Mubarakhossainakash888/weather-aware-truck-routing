// Recompute a route's risk summary for the slider-shifted forecast hour,
// using the same miles-weighted math as the backend (recommend.py):
// each checkpoint covers cp.miles_covered miles at its shifted risk level.
function shiftedSummary(route, forecastHour) {
  if (!forecastHour) return route.risk_summary;
  const milesByLevel = { Low: 0, Moderate: 0, High: 0, Severe: 0, 'No Travel': 0 };
  let weightedScore = 0;
  let totalMiles = 0;
  for (const cp of route.checkpoints) {
    const step = cp.slider?.[forecastHour];
    if (!step) continue;
    const covered = cp.miles_covered || 0;
    milesByLevel[step.risk_level] = (milesByLevel[step.risk_level] || 0) + covered;
    weightedScore += (step.risk_score || 0) * covered;
    totalMiles += covered;
  }
  if (totalMiles === 0) return route.risk_summary;
  const round1 = (n) => Math.round(n * 10) / 10;
  return {
    low_miles: round1(milesByLevel.Low),
    moderate_miles: round1(milesByLevel.Moderate),
    high_miles: round1(milesByLevel.High),
    severe_miles: round1(milesByLevel.Severe),
    no_travel_miles: round1(milesByLevel['No Travel']),
    avg_risk: Math.round((weightedScore / totalMiles) * 100) / 100,
  };
}

export default function RouteCards({ routes, selectedRouteId, onSelectRoute, forecastHour = 0 }) {
  if (!routes || routes.length === 0) return null;

  const recommendedRoute = routes.find((r) => r.is_recommended) || routes[0];

  return (
    <div className="card">
      <div className="section-title">
        <span>
          Route Options & Safety Ranking (Click a route to inspect)
          {forecastHour > 0 ? ` · +${forecastHour}h Forecast Shift` : ''}
        </span>
      </div>

      {forecastHour > 0 && (
        <p style={{ margin: '0 0 12px', fontSize: '0.85rem', color: '#475569' }}>
          Risk shown for the +{forecastHour}h shifted forecast. Recommendation ranking stays for the departure time.
        </p>
      )}

      {recommendedRoute.warning && (
        <div className="warning-banner" style={{ marginBottom: '14px' }}>
          <span>&#9888;</span>
          <span>{recommendedRoute.warning}</span>
        </div>
      )}

      <div className="routes-grid">
        {routes.map((route) => {
          const rs = shiftedSummary(route, forecastHour);
          const isSelected = route.id === selectedRouteId;

          return (
            <div
              key={route.id}
              onClick={() => onSelectRoute(route.id)}
              className={`route-card ${isSelected ? 'selected' : ''} ${
                route.is_recommended ? 'recommended' : ''
              }`}
            >
              <div className="route-card-top">
                <div>
                  <div className="route-name">
                    #{route.rank} — {route.name}
                  </div>
                  <small style={{ color: '#64748b' }}>
                    {route.checkpoints.length} checkpoints · Source: {route.source}
                  </small>
                </div>

                {route.is_recommended ? (
                  <span className="badge-rec">&#10003; Recommended</span>
                ) : (
                  <span className="badge-alt">Alternative #{route.rank}</span>
                )}
              </div>

              <div className="route-metrics">
                <span>
                  <strong>Distance:</strong> {route.distance_miles} mi
                </span>
                <span>
                  <strong>ETA Duration:</strong> {route.duration_formatted}
                </span>
                <span>
                  <strong>Avg Risk:</strong> {rs.avg_risk} / 4
                </span>
              </div>

              {route.is_recommended && route.recommendation_reason && (
                <div className="route-reason">{route.recommendation_reason}</div>
              )}

              <div className="miles-pills">
                <span className="pill low">Low: {rs.low_miles} mi</span>
                <span className="pill moderate">Mod: {rs.moderate_miles} mi</span>
                <span className="pill high">High: {rs.high_miles} mi</span>
                <span className="pill severe">Severe: {rs.severe_miles} mi</span>
                {rs.no_travel_miles > 0 && (
                  <span className="pill notravel">No Travel: {rs.no_travel_miles} mi</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}