import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000/api";

const http = axios.create({ baseURL: API_BASE, timeout: 10000 });

export async function fetchExpenses(params = {}) {
  const { data } = await http.get("/expenses", { params });
  return data;
}

export async function createExpense(payload) {
  const { data } = await http.post("/expenses", payload);
  return data;
}

export async function deleteExpense(id) {
  await http.delete(`/expenses/${id}`);
}

export async function fetchAnomalies() {
  const { data } = await http.get("/anomalies");
  return data;
}

export async function fetchTrend(days = 30) {
  const { data } = await http.get("/stats/trend", { params: { days } });
  return data;
}

export async function fetchByCategory(days = 30) {
  const { data } = await http.get("/stats/by-category", { params: { days } });
  return data;
}

export async function fetchHealth() {
  const { data } = await http.get("/health");
  return data;
}

export { API_BASE };