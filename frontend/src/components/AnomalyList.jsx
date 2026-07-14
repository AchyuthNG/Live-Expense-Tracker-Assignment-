const severityColors = {
  high: "#dc2626",
  medium: "#f59e0b",
  low: "#3b82f6",
};

export default function AnomalyList({ anomalies }) {
  if (!anomalies || anomalies.length === 0) {
    return (
      <div className="chart-card">
        <h3>Anomaly Alerts</h3>
        <p className="empty">No anomalies detected yet.</p>
      </div>
    );
  }

  return (
    <div className="chart-card">
      <h3>Anomaly Alerts ({anomalies.length})</h3>
      <ul className="anomaly-list">
        {anomalies.map((a) => {
          const color = severityColors[a.severity] || "#888";
          return (
            <li key={a.id} style={{ borderLeftColor: color }}>
              <div className="anomaly-head">
                <span className="badge" style={{ borderColor: color, color }}> 
                  {a.severity}
                </span>
                <span className="muted">{a.expense?.category || "—"}</span>
                <span className="num muted">
                  {a.expense ? `₹${Number(a.expense.amount).toFixed(2)}` : ""}
                </span>
                <span className="muted small">{a.rule_triggered}</span>
              </div>
              <div className="anomaly-reason">{a.reason}</div>
              <div className="muted small">
                {new Date(a.detected_at).toLocaleString()}
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}