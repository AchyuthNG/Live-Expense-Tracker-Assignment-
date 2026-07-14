import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from "recharts";

const COLORS = [
  "#60a5fa", "#f472b6", "#34d399", "#fbbf24",
  "#a78bfa", "#fb7185", "#22d3ee",
];

const COLOR_MAP = {
  groceries: "#60a5fa",
  travel: "#f472b6",
  rent: "#34d399",
  student_loan: "#fbbf24",
  shopping: "#a78bfa",
  food: "#fb7185",
  misc: "#22d3ee",
};

export default function CategoryPie({ data }) {
  if (!data || data.length === 0) {
    return <p className="empty">No category breakdown for this period yet.</p>;
  }

  return (
    <div className="chart-card">
      <h3>Spend by Category</h3>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            dataKey="total"
            nameKey="category"
            cx="50%"
            cy="50%"
            outerRadius={100}
            label={(entry) => entry.category}
          >
            {data.map((entry) => (
              <Cell
                key={entry.category}
                fill={COLOR_MAP[entry.category] || COLORS[data.indexOf(entry) % COLORS.length]}
              />
            ))}
          </Pie>
          <Tooltip formatter={(v) => `₹${Number(v).toFixed(2)}`} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}