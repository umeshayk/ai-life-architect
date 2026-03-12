import { useEffect, useState } from "react";
import api from "../api/client";

export default function Dashboard({ user }) {
  const [insights, setInsights] = useState(null);

  useEffect(() => {
    api
      .get("/api/ai/weekly-insights")
      .then((response) => setInsights(response.data))
      .catch(() => setInsights(null));
  }, []);

  return (
    <div className="stack">
      <section className="card">
        <h2>Welcome back, {user?.full_name}</h2>
        <p className="muted">Track recent knowledge activity and jump into your saved context.</p>
      </section>
      <section className="card dashboard-grid">
        <div>
          <h3>Total Items</h3>
          <p className="metric">{insights?.total_items ?? "-"}</p>
        </div>
        <div>
          <h3>Added This Week</h3>
          <p className="metric">{insights?.items_added_this_week ?? "-"}</p>
        </div>
      </section>
      <section className="card">
        <h3>Top Tags</h3>
        <div className="tag-list">
          {(insights?.top_tags || []).map((tag) => (
            <span key={tag} className="tag">{tag}</span>
          ))}
        </div>
      </section>
      <section className="card">
        <h3>Recent Titles</h3>
        <ul className="simple-list">
          {(insights?.recent_titles || []).map((title) => (
            <li key={title}>{title}</li>
          ))}
        </ul>
      </section>
    </div>
  );
}
