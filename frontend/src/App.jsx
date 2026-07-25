import React, { useState } from "react";
import TripForm from "./components/TripForm.jsx";
import MapView from "./components/MapView.jsx";
import StopsList from "./components/StopsList.jsx";
import LogSheetsView from "./components/LogSheetsView.jsx";
import { planTrip } from "./api.js";

export default function App() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(formValues) {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await planTrip(formValues);
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>ELD Trip Planner</h1>
        <p>Enter a trip and get a route plus FMCSA-style daily log sheets.</p>
      </header>

      <TripForm onSubmit={handleSubmit} loading={loading} />

      {error && <div className="error-banner">{error}</div>}

      {result && (
        <div className="results">
          <div className="summary-card">
            <div>
              <span className="label">Cycle used before trip</span>
              <span className="value">{result.summary.cycle_used_before_trip}h</span>
            </div>
            <div>
              <span className="label">Cycle used after trip</span>
              <span className="value">{result.summary.cycle_used_after_trip}h</span>
            </div>
            <div>
              <span className="label">Trip length</span>
              <span className="value">{result.summary.num_days} day(s)</span>
            </div>
          </div>

          <MapView route={result.route} />
          <StopsList stops={result.stops} />
          <LogSheetsView dailyLogs={result.daily_logs} />
        </div>
      )}
    </div>
  );
}
