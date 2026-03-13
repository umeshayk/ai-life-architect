import { useNavigate } from "react-router-dom";

export default function IngestionSummaryCard({ summary, title = "Upload Processed" }) {
  const navigate = useNavigate();

  if (!summary) {
    return null;
  }

  const primaryTopic = summary.normalized_topics?.[0] || summary.extracted_topics?.[0] || "";

  return (
    <section className="card ingestion-summary-card">
      <div className="row-between ingestion-summary-header">
        <div>
          <h3>{title}</h3>
          <p className="muted">Your content was processed and added to the knowledge graph.</p>
        </div>
        {summary.graph_updated ? <span className="tag">Graph Updated</span> : <span className="tag">Saved for Review</span>}
      </div>

      <div className="ingestion-summary-grid">
        <div className="ingestion-summary-section">
          <p className="source-meta">Extracted Topics</p>
          {summary.extracted_topics?.length ? (
            <div className="tag-list">
              {summary.extracted_topics.map((topic) => (
                <span key={`extracted-${topic}`} className="tag">{topic}</span>
              ))}
            </div>
          ) : (
            <p className="muted">No strong extracted topics yet.</p>
          )}
        </div>

        <div className="ingestion-summary-section">
          <p className="source-meta">Normalized Topics</p>
          {summary.normalized_topics?.length ? (
            <div className="tag-list">
              {summary.normalized_topics.map((topic) => (
                <button
                  key={`normalized-${topic}`}
                  type="button"
                  className="tag tag-button"
                  onClick={() => navigate(`/topics/${encodeURIComponent(topic)}`)}
                >
                  {topic}
                </button>
              ))}
            </div>
          ) : (
            <p className="muted">No graph topics were attached automatically.</p>
          )}
        </div>
      </div>

      {summary.learning_paths_affected?.length > 0 && (
        <div className="ingestion-summary-section">
          <p className="source-meta">Updated Learning Paths</p>
          <div className="stack compact">
            {summary.learning_paths_affected.map((path) => (
              <div key={path.path_name} className="related-item ingestion-path-row">
                <strong>{path.path_name}</strong>
                <p className="muted">
                  {path.covered_before}/{path.total_count} -&gt; {path.covered_after}/{path.total_count} completed
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {summary.suggested_next_topics?.length > 0 && (
        <div className="ingestion-summary-section">
          <p className="source-meta">Suggested Next Topic</p>
          <div className="tag-list">
            {summary.suggested_next_topics.map((topic) => (
              <button
                key={`next-${topic}`}
                type="button"
                className="tag tag-button"
                onClick={() => navigate(`/knowledge?topic=${encodeURIComponent(topic)}`)}
              >
                {topic}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="action-row ingestion-summary-actions">
        <button type="button" onClick={() => navigate("/brain-map")}>View in Brain Map</button>
        {primaryTopic && (
          <button type="button" className="secondary-button" onClick={() => navigate(`/topics/${encodeURIComponent(primaryTopic)}`)}>
            Open Topic
          </button>
        )}
        <button type="button" className="secondary-button" onClick={() => navigate("/knowledge")}>
          Add More Notes
        </button>
      </div>
    </section>
  );
}
