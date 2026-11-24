export default function CheckpointTable({ route }) {
  if (!route) return null;

  return (
    <div className="card">
      <div className="section-title">
        <span>
          Checkpoint Weather & Risk Breakdown — {route.name} ({route.distance_miles} mi)
        </span>
      </div>

      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Mile Marker</th>
              <th>Estimated Arrival (ETA)</th>
              <th>Wind (mph)</th>
              <th>Rain (in/hr)</th>
              <th>Snow (in/hr)</th>
              <th>Risk Level</th>
              <th>Rule Evaluation</th>
            </tr>
          </thead>
          <tbody>
            {route.checkpoints.map((cp) => {
              const badgeClass = `risk-badge risk-${cp.risk.level.replace(/\s+/g, '')}`;
              return (
                <tr key={cp.index}>
                  <td>{cp.index}</td>
                  <td>{cp.distance_miles} mi</td>
                  <td>{cp.eta_short}</td>
                  <td>{cp.weather.wind_mph} mph</td>
                  <td>{cp.weather.rain_in} in/hr</td>
                  <td>{cp.weather.snow_in} in/hr</td>
                  <td>
                    <span className={badgeClass}>{cp.risk.level}</span>
                  </td>
                  <td style={{ color: '#475569' }}>{cp.risk.reasons.join('; ')}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}