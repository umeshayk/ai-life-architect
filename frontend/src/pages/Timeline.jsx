import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import api from "../api/client";

const RANGE_OPTIONS = [
  { value: "7d", label: "Last 7 days" },
  { value: "30d", label: "Last 30 days" },
  { value: "all", label: "All time" }
];

const GROUP_OPTIONS = [
  { value: "day", label: "Day" },
  { value: "week", label: "Week" },
  { value: "month", label: "Month" }
];

function formatCreatedAt(value) {
  return new Date(value).toLocaleString([], {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit"
  });
}

function typeLabel(value) {
  if (value === "file") return "File";
  if (value === "link") return "Link";
  return "Note";
}

export default function Timeline() {
  const [range, setRange] = useState("30d");
  const [groupBy, setGroupBy] = useState("week");
  const [timeline, setTimeline] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadTimeline = async (nextRange = range, nextGroupBy = groupBy) => {
    setLoading(true);
    setError("");
    try {
      const response = await api.get("/api/timeline", {
        params: { range: nextRange, group_by: nextGroupBy }
      });
      setTimeline(response.data);
    } catch {
      setError("Unable to load the memory timeline right now.");
      setTimeline(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTimeline();
  }, [range, groupBy]);

  const summary = timeline?.summary;
  const insights = timeline?.insights;
  const groups = timeline?.groups || [];
  const topTopics = timeline?.top_topics || [];
  const hasItems = useMemo(() => groups.some((group) => group.count > 0), [groups]);

  return (
    <div className="stack">
      <section className="card">
        <h2>Memory Timeline</h2>
        <p className="muted">Explore how your saved knowledge has evolved over time.</p>
      </section>

      <section className="card timeline-controls">
        <div>
          <label htmlFor="timeline-range">Range</label>
          <select id="timeline-range" value={range} onChange={(event) => setRange(event.target.value)}>
            {RANGE_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="timeline-group-by">Group By</label>
          <select id="timeline-group-by" value={groupBy} onChange={(event) => setGroupBy(event.target.value)}>
            {GROUP_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
        </div>
      </section>

      <section className="card dashboard-grid">
        <div>
          <h3>Total Items</h3>
          <p className="metric">{summary?.total_items ?? "-"}</p>
        </div>
        <div>
          <h3>Most Active Period</h3>
          <p className="timeline-summary-value">{summary?.most_active_period ?? "-"}</p>
        </div>
        <div>
          <h3>Top Topics</h3>
          <p className="timeline-summary-value">{summary?.top_topics?.join(", ") || "-"}</p>
        </div>
        <div>
          <h3>Latest Saved</h3>
          <p className="timeline-summary-value">{summary?.latest_item_title || "-"}</p>
        </div>
      </section>

      <section className="card">
        <h3>AI Insight Summary</h3>
        <p className="timeline-insight-copy">{insights?.summary || "Not enough activity yet to generate insights."}</p>
        <div className="timeline-insight-grid">
          <div>
            <h4>Dominant Topic</h4>
            <p className="timeline-summary-value">{insights?.dominant_topic || "-"}</p>
          </div>
          <div>
            <h4>Emerging Topics</h4>
            {insights?.emerging_topics?.length ? (
              <div className="tag-list">
                {insights.emerging_topics.map((topic) => (
                  <span key={topic} className="tag">{topic}</span>
                ))}
              </div>
            ) : (
              <p className="muted">No emerging topics detected yet.</p>
            )}
          </div>
        </div>
        {!!insights?.suggestions?.length && (
          <>
            <h4>Suggestions</h4>
            <ul className="simple-list">
              {insights.suggestions.map((suggestion) => (
                <li key={suggestion}>{suggestion}</li>
              ))}
            </ul>
          </>
        )}
      </section>

      <section className="card">
        <h3>Top Topics in This Period</h3>
        <div className="tag-list">
          {topTopics.length ? (
            topTopics.map((topic) => (
              <span key={topic.name} className="tag">
                {topic.name} ({topic.count})
              </span>
            ))
          ) : (
            <p className="muted">No topics yet for this range.</p>
          )}
        </div>
      </section>

      {loading ? (
        <section className="card">
          <p>Loading timeline...</p>
        </section>
      ) : error ? (
        <section className="card">
          <p className="error-text">{error}</p>
        </section>
      ) : !hasItems ? (
        <section className="card">
          <p className="muted">No saved knowledge in this period yet.</p>
        </section>
      ) : (
        <div className="timeline-list">
          {groups.map((group) => (
            <section key={group.date_key} className="card timeline-group-card">
              <div className="row-between">
                <div>
                  <h3>{group.label}</h3>
                  <p className="muted">{group.date_key}</p>
                </div>
                <span className="tag">{group.count} items</span>
              </div>

              <div className="stack compact">
                {group.items.map((item) => (
                  <article key={item.id} className="result-item timeline-item">
                    <div className="row-between timeline-item-header">
                      <div>
                        <h4 className="timeline-item-title">
                          <Link to={`/knowledge?focus=${item.id}`} className="link-button">
                            {item.title}
                          </Link>
                        </h4>
                        <p className="source-meta">
                          {typeLabel(item.type)} | {formatCreatedAt(item.created_at)}
                        </p>
                      </div>
                      <span className="tag">{typeLabel(item.type)}</span>
                    </div>

                    {item.summary && <p>{item.summary}</p>}

                    {!!item.topics.length && (
                      <div className="tag-list">
                        {item.topics.map((topic) => (
                          <span key={`${item.id}-${topic}`} className="tag">{topic}</span>
                        ))}
                      </div>
                    )}

                    {!!item.tags.length && (
                      <div className="tag-list">
                        {item.tags.map((tag) => (
                          <span key={`${item.id}-${tag}`} className="tag">{tag}</span>
                        ))}
                      </div>
                    )}
                  </article>
                ))}
              </div>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}
