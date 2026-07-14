import { useCallback, useMemo } from "react";
import usePolling from "./hooks/usePolling";
import {
  fetchExpenses, fetchAnomalies, fetchTrend, fetchByCategory, deleteExpense,
} from "./api/client";
import ExpenseForm from "./components/ExpenseForm";
import ExpenseTable from "./components/ExpenseTable";
import TrendChart from "./components/TrendChart";
import CategoryPie from "./components/CategoryPie";
import AnomalyList from "./components/AnomalyList";

export default function App() {
  // Each poll uses a memoised function so the hook's effect doesn't reset.
  const { data: expenses, refresh: refreshExpenses } = usePolling(useCallback(() => fetchExpenses(), []), 8000);
  const { data: anomalies, refresh: refreshAnomalies } = usePolling(useCallback(() => fetchAnomalies(), []), 8000);
  const { data: trend, refresh: refreshTrend } = usePolling(useCallback(() => fetchTrend(30), []), 8000);
  const { data: categoryTotals, refresh: refreshCategory } = usePolling(useCallback(() => fetchByCategory(30), []), 8000);

  // After a successful POST, trigger an immediate re-fetch of everything.
  const handleCreated = useCallback(() => {
    refreshExpenses();
    refreshAnomalies();
    refreshTrend();
    refreshCategory();
  }, [refreshExpenses, refreshAnomalies, refreshTrend, refreshCategory]);

  const handleDelete = useCallback(async (id) => {
    try {
      await deleteExpense(id);
      handleCreated();
    } catch (err) {
      console.error("Delete failed", err);
    }
  }, [handleCreated]);

  const totalThisMonth = useMemo(() => {
    if (!expenses || expenses.length === 0) return 0;
    return expenses.reduce((s, e) => s + Number(e.amount), 0);
  }, [expenses]);

  return (
    <div className="app">
      <header>
        <h1>Live Expense Tracker</h1>
        <span className="tag">with anomaly alerts</span>
      </header>

      <section className="summary">
        <div className="stat-card">
          <span className="stat-label">Expenses logged</span>
          <span className="stat-value">{expenses ? expenses.length : 0}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Total shown</span>
          <span className="stat-value">₹{totalThisMonth.toFixed(2)}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Anomalies</span>
          <span className="stat-value">{anomalies ? anomalies.length : 0}</span>
        </div>
      </section>

      <section className="form-section">
        <ExpenseForm onCreated={handleCreated} />
      </section>

      <section className="charts">
        <TrendChart data={trend} />
        <CategoryPie data={categoryTotals} />
      </section>

      <section className="table-section">
        <h3>Recent Expenses</h3>
        <ExpenseTable expenses={expenses} onDelete={handleDelete} />
      </section>

      <section className="anomaly-section">
        <AnomalyList anomalies={anomalies} />
      </section>

      <footer>
        <span className="muted small">
          Polling every 8s · FastAPI + React + PostgreSQL · Docker Compose
        </span>
      </footer>
    </div>
  );
}