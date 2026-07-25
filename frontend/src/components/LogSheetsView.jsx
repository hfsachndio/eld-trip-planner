import React from "react";
import LogSheet from "./LogSheet.jsx";

export default function LogSheetsView({ dailyLogs }) {
  if (!dailyLogs || dailyLogs.length === 0) return null;

  return (
    <div className="log-sheets-view">
      <h2>ELD Daily Log Sheets</h2>
      {dailyLogs.map((log, i) => (
        <LogSheet key={log.date} log={log} dayNumber={i + 1} totalDays={dailyLogs.length} />
      ))}
    </div>
  );
}
