import { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

const RISK_COLORS = {
  Low: '#16a34a',
  Moderate: '#eab308',
  High: '#f97316',
  Severe: '#dc2626',
  'No Travel': '#7f1d1d',
};

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

export default function RouteMap({
  origin,
  destination,
  routes,
  selectedRouteId,
  onSelectRoute,
  forecastHour,
  onForecastHourChange,
}) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const routesLayerRef = useRef(null);
  const heatmapLayerRef = useRef(null);
  const markersLayerRef = useRef(null);
  const boundsRef = useRef(null);
  const hasFittedInitialRef = useRef(false);

  const [showHeatmap, setShowHeatmap] = useState(true);

  const selectedRoute = routes.find((r) => r.id === selectedRouteId) || routes[0];

  useEffect(() => {
    const container = mapContainerRef.current;
    if (!container || mapInstanceRef.current) return;

    const map = L.map(container, {
      center: [39.8283, -98.5795],
      zoom: 4,
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      maxZoom: 18,
    }).addTo(map);

    heatmapLayerRef.current = L.layerGroup().addTo(map);
    routesLayerRef.current = L.layerGroup().addTo(map);
    markersLayerRef.current = L.layerGroup().addTo(map);
    mapInstanceRef.current = map;

    const observer = new ResizeObserver(() => {
      map.invalidateSize({ animate: false });
      if (boundsRef.current && !hasFittedInitialRef.current) {
        map.fitBounds(boundsRef.current, { padding: [36, 36], animate: false });
        hasFittedInitialRef.current = true;
      }
    });
    observer.observe(container);

    return () => {
      observer.disconnect();
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Effect 1: Draw route polylines and fit bounds ONLY when routes/selection change (not on slider change)
  useEffect(() => {
    const map = mapInstanceRef.current;
    const routesLayer = routesLayerRef.current;
    if (!map || !routesLayer || !routes?.length) return;

    routesLayer.clearLayers();
    const allBounds = [];

    const orderedRoutes = [
      ...routes.filter((r) => r.id !== selectedRouteId),
      ...routes.filter((r) => r.id === selectedRouteId),
    ];

    orderedRoutes.forEach((route) => {
      const isSelected = route.id === selectedRouteId;
      const latLngs = route.coordinates.map(([lon, lat]) => [lat, lon]);
      allBounds.push(...latLngs);

      const lineColor = isSelected
        ? route.is_recommended
          ? '#16a34a'
          : '#2563eb'
        : '#64748b';

      const polyline = L.polyline(latLngs, {
        color: lineColor,
        weight: isSelected ? 6 : 4,
        opacity: isSelected ? 0.92 : 0.45,
        dashArray: isSelected ? null : '8, 8',
      });

      polyline.bindTooltip(
        `${route.name} (${route.distance_miles} mi · ${route.duration_formatted})`,
        { sticky: true }
      );
      polyline.on('click', () => onSelectRoute(route.id));
      polyline.addTo(routesLayer);
    });

    if (allBounds.length > 0) {
      const leafletBounds = L.latLngBounds(allBounds);
      boundsRef.current = leafletBounds;
      hasFittedInitialRef.current = false;
      requestAnimationFrame(() => {
        map.invalidateSize({ animate: false });
        map.fitBounds(leafletBounds, { padding: [36, 36] });
        hasFittedInitialRef.current = true;
      });
      // The rAF fit can run while the results panel is still mounting
      // (container not laid out yet), leaving the map on the world view.
      // Re-fit once more after layout settles.
      const refitTimer = setTimeout(() => {
        map.invalidateSize({ animate: false });
        map.fitBounds(leafletBounds, { padding: [36, 36], animate: false });
        hasFittedInitialRef.current = true;
      }, 500);
      return () => clearTimeout(refitTimer);
    }
  }, [routes, selectedRouteId, onSelectRoute]);

  // Effect 2: Update checkpoint markers, popups, and heatmap overlay when forecastHour or selectedRoute changes
  useEffect(() => {
    const markersLayer = markersLayerRef.current;
    const heatmapLayer = heatmapLayerRef.current;
    if (!markersLayer || !heatmapLayer) return;

    markersLayer.clearLayers();
    heatmapLayer.clearLayers();

    if (origin) {
      L.circleMarker([origin.lat, origin.lon], {
        radius: 8,
        color: '#0f172a',
        weight: 2,
        fillColor: '#38bdf8',
        fillOpacity: 1,
      })
        .bindPopup(`<strong>Origin:</strong> ${origin.name}`)
        .addTo(markersLayer);
    }

    if (destination) {
      L.circleMarker([destination.lat, destination.lon], {
        radius: 8,
        color: '#0f172a',
        weight: 2,
        fillColor: '#a855f7',
        fillOpacity: 1,
      })
        .bindPopup(`<strong>Destination:</strong> ${destination.name}`)
        .addTo(markersLayer);
    }

    if (selectedRoute) {
      selectedRoute.checkpoints.forEach((cp) => {
        const step = cp.slider?.[forecastHour];
        const activeLevel = step ? step.risk_level : cp.risk.level;
        const activeWind = step ? step.wind_mph : cp.weather.wind_mph;
        const activeRain = step ? step.rain_in : cp.weather.rain_in;
        const activeSnow = step ? step.snow_in : cp.weather.snow_in;
        const color = RISK_COLORS[activeLevel] || '#16a34a';
        const localEtaLabel = formatLocalEta(cp.eta, forecastHour);

        const marker = L.circleMarker([cp.lat, cp.lon], {
          radius: 6,
          color: '#ffffff',
          weight: 2,
          fillColor: color,
          fillOpacity: 0.95,
        });

        marker.bindPopup(`
          <div style="font-size:13px; line-height:1.45; min-width:195px;">
            <strong>Checkpoint #${cp.index} (${cp.distance_miles} mi)</strong><br/>
            <span><b>ETA (Local):</b> ${localEtaLabel}</span><br/>
            <span><b>Risk:</b> <span style="color:${color}; font-weight:700;">${activeLevel}</span></span><br/>
            <hr style="margin:5px 0; border:none; border-top:1px solid #e2e8f0;"/>
            <span><b>Wind:</b> ${activeWind} mph</span><br/>
            <span><b>Rain:</b> ${activeRain} in/hr</span><br/>
            <span><b>Snow:</b> ${activeSnow} in/hr</span><br/>
            <small style="color:#475569;">${cp.risk.reasons.join('; ')}</small>
          </div>
        `);

        marker.addTo(markersLayer);

        if (showHeatmap) {
          L.circle([cp.lat, cp.lon], {
            radius: 24000,
            stroke: false,
            fillColor: color,
            fillOpacity: 0.28,
            interactive: false,
          }).addTo(heatmapLayer);
        }
      });
    }
  }, [origin, destination, selectedRoute, forecastHour, showHeatmap]);

  return (
    <div className="card">
      <div className="section-title">
        <span>Interactive Route Map & 0–48h Weather Corridor Heatmap</span>
        <label style={{ fontSize: '0.84rem', fontWeight: 600, cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={showHeatmap}
            onChange={(e) => setShowHeatmap(e.target.checked)}
            style={{ marginRight: '6px' }}
          />
          Show Corridor Heatmap
        </label>
      </div>

      <div className="map-controls">
        <div className="slider-box">
          <label htmlFor="forecast-slider">Forecast Shift (0–48h):</label>
          <input
            id="forecast-slider"
            type="range"
            min="0"
            max="48"
            value={forecastHour}
            onChange={(e) => onForecastHourChange(Number(e.target.value))}
          />
          <span className="hour-tag">+{forecastHour} hrs</span>
        </div>

        <div className="legend-bar">
          <span className="legend-item">
            <i className="legend-dot" style={{ background: '#16a34a' }} /> Low
          </span>
          <span className="legend-item">
            <i className="legend-dot" style={{ background: '#eab308' }} /> Moderate
          </span>
          <span className="legend-item">
            <i className="legend-dot" style={{ background: '#f97316' }} /> High
          </span>
          <span className="legend-item">
            <i className="legend-dot" style={{ background: '#dc2626' }} /> Severe
          </span>
          <span className="legend-item">
            <i className="legend-dot" style={{ background: '#7f1d1d' }} /> No Travel
          </span>
        </div>
      </div>

      <div ref={mapContainerRef} className="map-wrapper" />
    </div>
  );
  
}