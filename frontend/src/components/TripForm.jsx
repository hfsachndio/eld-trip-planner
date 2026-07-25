import React, { useState } from "react";

export default function TripForm({ onSubmit, loading }) {
  const [currentLocation, setCurrentLocation] = useState("");
  const [pickupLocation, setPickupLocation] = useState("");
  const [dropoffLocation, setDropoffLocation] = useState("");
  const [cycleUsed, setCycleUsed] = useState("");

  function handleSubmit(e) {
    e.preventDefault();
    onSubmit({
      currentLocation,
      pickupLocation,
      dropoffLocation,
      currentCycleUsedHours: Number(cycleUsed || 0),
    });
  }

  return (
    <form className="trip-form" onSubmit={handleSubmit}>
      <div className="field">
        <label htmlFor="current">Current Location</label>
        <input
          id="current"
          type="text"
          placeholder="e.g. Dallas, TX"
          value={currentLocation}
          onChange={(e) => setCurrentLocation(e.target.value)}
          required
        />
      </div>

      <div className="field">
        <label htmlFor="pickup">Pickup Location</label>
        <input
          id="pickup"
          type="text"
          placeholder="e.g. Oklahoma City, OK"
          value={pickupLocation}
          onChange={(e) => setPickupLocation(e.target.value)}
          required
        />
      </div>

      <div className="field">
        <label htmlFor="dropoff">Dropoff Location</label>
        <input
          id="dropoff"
          type="text"
          placeholder="e.g. Chicago, IL"
          value={dropoffLocation}
          onChange={(e) => setDropoffLocation(e.target.value)}
          required
        />
      </div>

      <div className="field">
        <label htmlFor="cycle">Current Cycle Used (Hrs, 70hr/8day)</label>
        <input
          id="cycle"
          type="number"
          min="0"
          max="70"
          step="0.5"
          placeholder="e.g. 12"
          value={cycleUsed}
          onChange={(e) => setCycleUsed(e.target.value)}
          required
        />
      </div>

      <button type="submit" disabled={loading}>
        {loading ? "Planning trip..." : "Plan Trip"}
      </button>
    </form>
  );
}
