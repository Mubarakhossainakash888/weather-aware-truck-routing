function formatLocalEta(etaIso, shiftHours = 0) {
  if (!etaIso) return '';
  const normalized = etaIso.endsWith('Z') || etaIso.includes('+') ? etaIso : `${etaIso}Z`;
  const dt = new Date(normalized);
  if (Number.isNaN(dt.getTime())) return etaIso;
  dt.setHours(dt.getHours() + shiftHours);
  return dt.toLocaleString([], {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function CheckpointTable({ route, forecastHour = 0 }) {
  if (!route) return null;

  return (
    <div className="card">
      <div className="section-title">
        <span>
          Checkpoint Weather & Risk Breakdown — {route.name} ({route.distance_miles} mi)
          {forecastHour > 0 ? ` · +${forecastHour}h Forecast Shift` : ''}
        </span>
      </div>

      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Mile Marker</th>
              <th>Estimated Arrival (Local)</th>
              <th>Wind (mph)</th>
              <th>Rain (in/hr)</th>
              <th>Snow (in/hr)</th>
              <th>Risk Level</th>
              <th>Rule Evaluation</th>
            </tr>
          </thead>
          <tbody>
            {route.checkpoints.map((cp) => {
              const step = cp.slider?.[forecastHour];
              const activeLevel = step ? step.risk_level : cp.risk.level;
              const activeWind = step ? step.wind_mph : cp.weather.wind_mph;
              const activeRain = step ? step.rain_in : cp.weather.rain_in;
              const activeSnow = step ? step.snow_in : cp.weather.snow_in;
              const localEta = formatLocalEta(cp.eta, forecastHour);
              const badgeClass = `risk-badge risk-${activeLevel.replace(/\s+/g, '')}`;

              return (
                <tr key={cp.index}>
                  <td>{cp.index}</td>
                  <td>{cp.distance_miles} mi</td>
                  <td>{localEta}</td>
                  <td>{activeWind} mph</td>
                  <td>{activeRain} in/hr</td>
                  <td>{activeSnow} in/hr</td>
                  <td>
                    <span className={badgeClass}>{activeLevel}</span>
                  </td>
                  <td style={{ color: '#475569' }}>
                    {forecastHour > 0 && activeLevel !== cp.risk.level
                      ? `Shifted (+${forecastHour}h): ${activeWind} mph wind, ${activeRain} in/hr rain, ${activeSnow} in/hr snow`
                      : cp.risk.reasons.join('; ')}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}