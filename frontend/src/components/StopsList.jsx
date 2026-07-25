import React from "react";

function formatTime(iso) {
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function StopsList({ stops }) {
  if (!stops || stops.length === 0) return null;

  return (
    <div className="stops-list">
      <h3>Stops &amp; Rests</h3>
      <ul>
        {stops.map((s, i) => (
          <li key={i}>
            <span className="stop-time">{formatTime(s.time)}</span>
            <span className="stop-remark">{s.remark}</span>
            <span className="stop-duration">{s.duration_hours} hr</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
