import React from "react";
import { MapContainer, TileLayer, Marker, Polyline, Popup, useMap } from "react-leaflet";
import L from "leaflet";

import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";

const defaultIcon = L.icon({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

function FitBounds({ positions }) {
  const map = useMap();
  React.useEffect(() => {
    if (positions.length > 0) {
      map.fitBounds(positions, { padding: [40, 40] });
    }
  }, [positions, map]);
  return null;
}

export default function MapView({ route }) {
  if (!route) return null;

  const { geometry, points } = route;
  // GeoJSON LineString coordinates are [lon, lat]; Leaflet wants [lat, lon]
  const positions = geometry.coordinates.map(([lon, lat]) => [lat, lon]);

  const markers = [
    { ...points.current, color: "Current Location" },
    { ...points.pickup, color: "Pickup" },
    { ...points.dropoff, color: "Dropoff" },
  ];

  return (
    <div className="map-wrapper">
      <MapContainer center={positions[0]} zoom={6} style={{ height: "420px", width: "100%" }}>
        <TileLayer
          attribution='&copy; OpenStreetMap contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Polyline positions={positions} pathOptions={{ color: "#2563eb", weight: 4 }} />
        {markers.map((m, i) => (
          <Marker key={i} position={[m.lat, m.lon]} icon={defaultIcon}>
            <Popup>
              <strong>{m.color}</strong>
              <br />
              {m.label}
            </Popup>
          </Marker>
        ))}
        <FitBounds positions={positions} />
      </MapContainer>
      <p className="route-summary">
        Total distance: <strong>{route.total_distance_miles} mi</strong> &nbsp;|&nbsp; Total drive
        time: <strong>{route.total_drive_hours} hrs</strong>
      </p>
    </div>
  );
}
