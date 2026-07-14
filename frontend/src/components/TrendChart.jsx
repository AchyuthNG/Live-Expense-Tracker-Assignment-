import {
  ComposedChart, Scatter, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, Legend,
} from "recharts";

const fmtDate = (d) => {
  const date = new Date(d);
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
};

export default function TrendChart({ data }) {
  if (!data || data.length === 0) {
    return <p className="empty">No spending data for this period yet.</p>;
  }

  return (
    <div className="chart-card">
      <h3>Spending Trend (daily vs 7-day rolling avg)</h3>
      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#333" />
          <XAxis dataKey="date" tickFormatter={fmtDate} stroke="#888" />
          <YAxis stroke="#888" />
          <Tooltip labelFormatter={fmtDate} />
          <Legend />
          <Scatter name="Daily" dataKey="daily" fill="#60a5fa" />
          <Line
            name="Trend (7d avg)"
            type="monotone"
            dataKey="trend"
            stroke="#f472b6"
            strokeWidth={2}
            dot={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}