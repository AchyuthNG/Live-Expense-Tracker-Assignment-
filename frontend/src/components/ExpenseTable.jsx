const severityColors = {
  high: "#dc2626",
  medium: "#f59e0b",
  low: "#3b82f6",
  none: "transparent",
};

export default function ExpenseTable({ expenses, onDelete }) {
  if (!expenses || expenses.length === 0) {
    return <p className="empty">No expenses yet — add one above.</p>;
  }

  return (
    <table className="expense-table">
      <thead>
        <tr>
          <th>Date</th>
          <th>Category</th>
          <th className="num">Amount</th>
          <th>Description</th>
          <th>Flag</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {expenses.map((e) => {
          const anomaly = e.anomaly;
          const color = anomaly ? severityColors[anomaly.severity] : severityColors.none;
          return (
            <tr key={e.id} style={anomaly ? { background: `${color}11` } : {}}>
              <td>{e.expense_date}</td>
              <td className="cat">{e.category}</td>
              <td className="num">₹{Number(e.amount).toFixed(2)}</td>
              <td className="desc">{e.description || "—"}</td>
              <td>
                {anomaly ? (
                  <span className="badge" style={{ borderColor: color, color }}>
                    {anomaly.severity}
                  </span>
                ) : (
                  <span className="muted">—</span>
                )}
              </td>
              <td>
                <button className="del" onClick={() => onDelete(e.id)}>✕</button>
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}