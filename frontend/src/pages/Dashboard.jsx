import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/client";
import KnowledgeGrowth from "../components/KnowledgeGrowth";

export default function Dashboard({ user }) {
  const navigate = useNavigate();
  const [insights, setInsights] = useState(null);
  const [growth, setGrowth] = useState(null);
  const [discovering, setDiscovering] = useState(false);

  const loadInsights = async () => {
    try {
      const [insightsResponse, growthResponse] = await Promise.all([
        api.get("/api/insights/weekly"),
        api.get("/api/timeline/growth")
      ]);
      setInsights(insightsResponse.data);
      setGrowth(growthResponse.data);
    } catch {
      setInsights(null);
      setGrowth(null);
    }
  };

  useEffect(() => {
    loadInsights();
  }, []);

  const handleRediscoverTopics = async () => {
    setDiscovering(true);
    try {
      await api.post("/api/topics/discover");
      await loadInsights();
    } finally {
      setDiscovering(false);
    }
  };

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
        <div className="row-between">
          <h3>Top Topics</h3>
          <button type="button" className="secondary-button" onClick={handleRediscoverTopics}>
            {discovering ? "Discovering..." : "Rediscover Topics"}
          </button>
        </div>
        <div className="tag-list">
          {(insights?.top_topics || []).map((topic) => (
            <button
              key={topic.id || topic.name}
              type="button"
              className="tag tag-button"
              onClick={() => navigate(`/topics/${encodeURIComponent(topic.name)}`)}
            >
              {topic.name} ({topic.count})
            </button>
          ))}
        </div>
      </section>
      <section className="card">
        <h3>Top Tags</h3>
        <div className="tag-list">
          {(insights?.top_tags || []).map((tag, index) => (
            <span key={`${index}-${tag}`} className="tag">{tag}</span>
          ))}
        </div>
      </section>
      <section className="card">
        <h3>Recent Titles</h3>
        <ul className="simple-list">
          {(insights?.recent_titles || []).map((title, index) => (
            <li key={`${index}-${title}`}>{title}</li>
          ))}
        </ul>
      </section>
      <section className="card">
        <h3>Weekly Suggestions</h3>
        <ul className="simple-list">
          {(insights?.suggestions || []).map((suggestion, index) => (
            <li key={`${index}-${suggestion}`}>{suggestion}</li>
          ))}
        </ul>
      </section>
      <KnowledgeGrowth growth={growth} />
    </div>
  );
}
