export default function RouteCards({ routes, selectedRouteId, onSelectRoute }) {
  if (!routes || routes.length === 0) return null;

  const recommendedRoute = routes.find((r) => r.is_recommended) || routes[0];

  return (
    <div className="card">
      <div className="section-title">
        <span>Route Options & Safety Ranking (Click a route to inspect)</span>
      </div>

      {recommendedRoute.warning && (
        <div className="warning-banner" style={{ marginBottom: '14px' }}>
          <span>&#9888;</span>
          <span>{recommendedRoute.warning}</span>
        </div>
      )}

      <div className="routes-grid">
        {routes.map((route) => {
          const rs = route.risk_summary;
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