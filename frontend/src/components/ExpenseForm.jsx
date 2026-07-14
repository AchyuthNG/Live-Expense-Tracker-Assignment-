import { useState } from "react";
import { createExpense } from "../api/client";

const CATEGORIES = [
  "groceries", "travel", "rent", "student_loan", "shopping", "food", "misc",
];

export default function ExpenseForm({ onCreated }) {
  const today = new Date().toISOString().slice(0, 10);
  const [form, setForm] = useState({
    amount: "",
    category: "groceries",
    description: "",
    expense_date: today,
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await createExpense({
        amount: parseFloat(form.amount),
        category: form.category,
        description: form.description || null,
        expense_date: form.expense_date,
      });
      setForm((prev) => ({
        ...prev,
        amount: "",
        description: "",
      }));
      // Immediate re-fetch after a successful POST so the user's
      // own action feels instant instead of waiting for the next poll tick.
      if (onCreated) onCreated();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to save expense");
    } finally {
      setSubmitting(false);
    }
  };

  const field = (name) => ({
    name,
    value: form[name],
    onChange: (e) => setForm((p) => ({ ...p, [name]: e.target.value })),
  });

  return (
    <form className="expense-form" onSubmit={handleSubmit}>
      <h3>Add Expense</h3>
      {error && <div className="error">{error}</div>}
      <div className="row">
        <label>
          Amount
          <input type="number" step="0.01" min="0" required
            {...field("amount")} placeholder="0.00" />
        </label>
        <label>
          Category
          <select {...field("category")}>
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </label>
      </div>
      <div className="row">
        <label>
          Date
          <input type="date" required {...field("expense_date")} />
        </label>
        <label>
          Description
          <input type="text" maxLength="255"
            {...field("description")} placeholder="optional note" />
        </label>
      </div>
      <button type="submit" disabled={submitting}>
        {submitting ? "Saving..." : "Add Expense"}
      </button>
    </form>
  );
}