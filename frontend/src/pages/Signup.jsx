import { useState } from "react";
import api from "../api/client";

export default function Signup({ onSuccess }) {
  const [form, setForm] = useState({ email: "", full_name: "", password: "" });
  const [error, setError] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    try {
      const response = await api.post("/auth/signup", form);
      onSuccess(response.data.access_token);
    } catch (err) {
      setError(err.response?.data?.detail || "Signup failed.");
    }
  };

  return (
    <div className="auth-card card">
      <h2>Sign Up</h2>
      <form onSubmit={handleSubmit} className="stack">
        <input
          placeholder="Full name"
          value={form.full_name}
          onChange={(event) => setForm({ ...form, full_name: event.target.value })}
        />
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
        <button type="submit">Create Account</button>
      </form>
    </div>
  );
}
