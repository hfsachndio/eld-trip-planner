import React from "react";

const STATUS_ORDER = ["Off Duty", "Sleeper Berth", "Driving", "On Duty (Not Driving)"];
const STATUS_SHORT = {
  "Off Duty": "1. Off Duty",
  "Sleeper Berth": "2. Sleeper Berth",
  Driving: "3. Driving",
  "On Duty (Not Driving)": "4. On Duty (Not Driving)",
};

const MARGIN_LEFT = 160;
const MARGIN_TOP = 30;
const GRID_WIDTH = 920;
const ROW_HEIGHT = 34;
const HOUR_WIDTH = GRID_WIDTH / 24;

function hourLabel(h) {
  const hr = h % 24;
  if (hr === 0) return "Mid night";
  if (hr === 12) return "Noon";
  return String(hr > 12 ? hr - 12 : hr);
}

export default function LogSheet({ log, dayNumber, totalDays }) {
  const rowY = {};
  STATUS_ORDER.forEach((status, i) => {
    rowY[status] = MARGIN_TOP + i * ROW_HEIGHT + ROW_HEIGHT / 2;
  });

  // Build the step-line points across the 24-hour grid.
  const points = [];
  log.segments.forEach((seg, idx) => {
    const x1 = MARGIN_LEFT + seg.start_hour * HOUR_WIDTH;
    const x2 = MARGIN_LEFT + seg.end_hour * HOUR_WIDTH;
    const y = rowY[seg.status_label];
    if (points.length === 0) {
      points.push(`${x1},${y}`);
    } else {
      // vertical jump from previous row to this row at the same x
      points.push(`${x1},${y}`);
    }
    points.push(`${x2},${y}`);
  });

  const totalHeight = MARGIN_TOP + STATUS_ORDER.length * ROW_HEIGHT + 20;
  const svgWidth = MARGIN_LEFT + GRID_WIDTH + 20;

  return (
    <div className="log-sheet">
      <div className="log-sheet-header">
        <h3>
          Driver's Daily Log &mdash; {log.date} (Day {dayNumber} of {totalDays})
        </h3>
      </div>
      <svg
        viewBox={`0 0 ${svgWidth} ${totalHeight + 30}`}
        width="100%"
        role="img"
        aria-label={`ELD daily log for ${log.date}`}
      >
        {/* Hour tick labels */}
        {Array.from({ length: 25 }).map((_, h) => (
          <text
            key={h}
            x={MARGIN_LEFT + h * HOUR_WIDTH}
            y={MARGIN_TOP - 10}
            fontSize="9"
            textAnchor="middle"
            fill="#334155"
          >
            {hourLabel(h)}
          </text>
        ))}

        {/* Vertical hour gridlines */}
        {Array.from({ length: 25 }).map((_, h) => (
          <line
            key={h}
            x1={MARGIN_LEFT + h * HOUR_WIDTH}
            y1={MARGIN_TOP}
            x2={MARGIN_LEFT + h * HOUR_WIDTH}
            y2={MARGIN_TOP + STATUS_ORDER.length * ROW_HEIGHT}
            stroke={h % 1 === 0 ? "#cbd5e1" : "#e2e8f0"}
            strokeWidth={h % 6 === 0 ? 1.2 : 0.6}
          />
        ))}

        {/* Row labels + horizontal lines */}
        {STATUS_ORDER.map((status, i) => {
          const yTop = MARGIN_TOP + i * ROW_HEIGHT;
          return (
            <g key={status}>
              <rect
                x={MARGIN_LEFT}
                y={yTop}
                width={GRID_WIDTH}
                height={ROW_HEIGHT}
                fill={i % 2 === 0 ? "#f8fafc" : "#ffffff"}
                stroke="#94a3b8"
                strokeWidth="0.6"
              />
              <text x={10} y={yTop + ROW_HEIGHT / 1.6} fontSize="11" fill="#0f172a">
                {STATUS_SHORT[status]}
              </text>
              <text
                x={MARGIN_LEFT + GRID_WIDTH + 10}
                y={yTop + ROW_HEIGHT / 1.6}
                fontSize="11"
                fill="#0f172a"
              >
                {log.totals[status] ?? 0}h
              </text>
            </g>
          );
        })}

        {/* The duty-status step line */}
        <polyline
          points={points.join(" ")}
          fill="none"
          stroke="#1d4ed8"
          strokeWidth="2.5"
          strokeLinejoin="round"
        />

        {/* Remarks */}
        {log.segments
          .filter((s) => s.remark)
          .map((s, i) => (
            <g key={i}>
              <line
                x1={MARGIN_LEFT + s.start_hour * HOUR_WIDTH}
                y1={MARGIN_TOP}
                x2={MARGIN_LEFT + s.start_hour * HOUR_WIDTH}
                y2={MARGIN_TOP + STATUS_ORDER.length * ROW_HEIGHT + 14}
                stroke="#dc2626"
                strokeWidth="0.7"
                strokeDasharray="2,2"
              />
              <text
                x={MARGIN_LEFT + s.start_hour * HOUR_WIDTH}
                y={MARGIN_TOP + STATUS_ORDER.length * ROW_HEIGHT + 26}
                fontSize="9"
                fill="#b91c1c"
                transform={`rotate(35, ${MARGIN_LEFT + s.start_hour * HOUR_WIDTH}, ${
                  MARGIN_TOP + STATUS_ORDER.length * ROW_HEIGHT + 26
                })`}
              >
                {s.remark}
              </text>
            </g>
          ))}
      </svg>
    </div>
  );
}
