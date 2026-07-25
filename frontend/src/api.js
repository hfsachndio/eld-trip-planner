const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function planTrip({
  currentLocation,
  pickupLocation,
  dropoffLocation,
  currentCycleUsedHours,
}) {
  const res = await fetch(`${API_BASE_URL}/api/plan-trip/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      current_location: currentLocation,
      pickup_location: pickupLocation,
      dropoff_location: dropoffLocation,
      current_cycle_used_hours: currentCycleUsedHours,
    }),
  });

  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.error || "Something went wrong while planning the trip.");
  }

  return data;
}
