import { useState } from 'react';

function getDefaultDeparture() {
  const now = new Date();
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
  return now.toISOString().slice(0, 16);
}

export default function TripForm({ onSubmit, loading }) {
  const [origin, setOrigin] = useState('Chicago, IL');
  const [destination, setDestination] = useState('Indianapolis, IN');
  const [departure, setDeparture] = useState(getDefaultDeparture);
  const [loadLb, setLoadLb] = useState(35000);
  const [intervalMi, setIntervalMi] = useState(25);

  const handleSubmit = (e) => {
    e.preventDefault();
    const utcDeparture = departure ? new Date(departure).toISOString() : new Date().toISOString();
    onSubmit({
      origin,
      destination,
      departure: utcDeparture,
      load_lb: Number(loadLb),
      interval_mi: Number(intervalMi),
    });
  };

  const applyPreset = (orig, dest, weight) => {
    setOrigin(orig);
    setDestination(dest);
    setLoadLb(weight);
  };

  return (
    <div className="card">
      <div className="section-title">
        <span>Trip Parameters & Truck Load</span>
      </div>

      <form className="trip-form" onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="origin">Origin</label>
          <input
            id="origin"
            type="text"
            value={origin}
            onChange={(e) => setOrigin(e.target.value)}
            placeholder="e.g. Chicago, IL"
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="destination">Destination</label>
          <input
            id="destination"
            type="text"
            value={destination}
            onChange={(e) => setDestination(e.target.value)}
            placeholder="e.g. Indianapolis, IN"
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="departure">Departure Date & Time</label>
          <input
            id="departure"
            type="datetime-local"
            value={departure}
            onChange={(e) => setDeparture(e.target.value)}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="loadWeight">Load Weight (lb)</label>
          <input
            id="loadWeight"
            type="number"
            min="1000"
            max="120000"
            step="500"
            value={loadLb}
            onChange={(e) => setLoadLb(e.target.value)}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="interval">Sample Interval</label>
          <select
            id="interval"
            value={intervalMi}
            onChange={(e) => setIntervalMi(Number(e.target.value))}
          >
            <option value={10}>Every 10 miles</option>
            <option value={25}>Every 25 miles</option>
            <option value={50}>Every 50 miles</option>
          </select>
        </div>

        <button type="submit" className="btn-submit" disabled={loading}>
          {loading ? 'Analyzing Routes...' : 'Find Safest Route'}
        </button>
      </form>

      <div className="presets-bar">
        <span>Quick Test Corridors:</span>
        <button
          type="button"
          className="preset-btn"
          onClick={() => applyPreset('Chicago, IL', 'Indianapolis, IN', 35000)}
        >
          Chicago → Indianapolis (35,000 lb)
        </button>
        <button
          type="button"
          className="preset-btn"
          onClick={() => applyPreset('Denver, CO', 'Cheyenne, WY', 45000)}
        >
          Denver → Cheyenne (45,000 lb)
        </button>
        <button
          type="button"
          className="preset-btn"
          onClick={() => applyPreset('Seattle, WA', 'Portland, OR', 28000)}
        >
          Seattle → Portland (28,000 lb)
        </button>
      </div>
    </div>
  );
}