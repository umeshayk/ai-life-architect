import { useState } from "react";
import api from "../api/client";

export default function Login({ onSuccess }) {
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    try {
      const response = await api.post("/auth/login", form);
      onSuccess(response.data.access_token);
    } catch (err) {
      setError(err.response?.data?.detail || "Login failed.");
    }
  };

  return (
    <div className="auth-card card">
      <h2>Log In</h2>
      <form onSubmit={handleSubmit} className="stack">
        <input
          placeholder="Email"
          type="email"
          value={form.email}
          onChange={(event) => setForm({ ...form, email: event.target.value })}
        />
        <input
          placeholder="Password"
          type="password"
          value={form.password}
          onChange={(event) => setForm({ ...form, password: event.target.value })}
        />
        {error && <p className="error-text">{error}</p>}
        <button type="submit">Log In</button>
      </form>
      <p className="muted">Use signup if this is your first time here.</p>
    </div>
  );
}
