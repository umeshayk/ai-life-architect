import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import api from "../api/client";

function formatTypeLabel(type) {
  return type ? type.charAt(0).toUpperCase() + type.slice(1) : "Note";
}

export default function Topic() {
  const { topic } = useParams();
  const [data, setData] = useState(null);
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState("");
  const [summaryError, setSummaryError] = useState("");
  const [loading, setLoading] = useState(true);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [refreshingSummary, setRefreshingSummary] = useState(false);

  const loadSummary = async (topicId, refresh = false) => {
    if (!topicId) {
      setSummary(null);
      setSummaryError("");
      return;
    }

    if (refresh) {
      setRefreshingSummary(true);
    } else {
      setSummaryLoading(true);
    }
    setSummaryError("");

    try {
      const response = await api.get(`/api/topics/${topicId}/summary`, { params: { refresh } });
      setSummary(response.data);
    } catch (err) {
      setSummary(null);
      setSummaryError(err.response?.data?.detail || "Unable to load the topic summary.");
    } finally {
      setSummaryLoading(false);
      setRefreshingSummary(false);
    }
  };

  useEffect(() => {
    const loadTopic = async () => {
      setLoading(true);
      setError("");
      setSummary(null);
      setSummaryError("");
      try {
        const response = await api.get("/api/topics/detail", {
          params: { name: topic }
        });
        setData(response.data);
        if (response.data?.topic_id) {
          loadSummary(response.data.topic_id);
        }
      } catch (err) {
        setError(err.response?.data?.detail || "Unable to load this topic.");
        setData(null);
      } finally {
        setLoading(false);
      }
    };

    if (topic) {
      loadTopic();
    }
  }, [topic]);

  return (
    <div className="stack">
      <section className="card">
        <h2>Topic: {data?.topic || topic}</h2>
        <p className="muted">Browse all notes connected to this topic.</p>
      </section>

      {loading ? (
        <section className="card">
          <p>Loading topic...</p>
        </section>
      ) : error ? (
        <section className="card">
          <p className="error-text">{error}</p>
        </section>
      ) : (
        <section className="dashboard-grid">
          <article className="card stack compact">
            <div className="row-between">
              <h3>Topic Summary</h3>
              {data?.topic_id ? (
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => loadSummary(data.topic_id, true)}
                  disabled={summaryLoading || refreshingSummary}
                >
                  {refreshingSummary ? "Refreshing..." : "Refresh Summary"}
                </button>
              ) : null}
            </div>
            {summaryLoading ? <p className="muted">Loading topic summary...</p> : null}
            {summaryError ? <p className="error-text">{summaryError}</p> : null}
            {summary ? (
              <>
                <p>{summary.summary}</p>
                <div>
                  <p className="source-meta">Why it matters</p>
                  <p className="muted">{summary.why_it_matters}</p>
                </div>
                {!!summary.skills_unlocked?.length && (
                  <div>
                    <p className="source-meta">Skills unlocked</p>
                    <div className="tag-list">
                      {summary.skills_unlocked.map((skill) => (
                        <Link key={skill} to={`/topics/${encodeURIComponent(skill)}`} className="tag tag-link">
                          {skill}
                        </Link>
                      ))}
                    </div>
                  </div>
                )}
                <p className="source-meta">Source: {summary.source === "ai" ? "AI" : "Rules"}</p>
              </>
            ) : (
              <p className="muted">No saved topic summary is available yet.</p>
            )}
          </article>

          <article className="card">
            <h3>Notes</h3>
            {data?.notes?.length ? (
              <div className="stack compact">
                {data.notes.map((note) => (
                  <article key={note.id} className="result-item">
                    <strong>{note.title}</strong>
                    <p className="muted">{formatTypeLabel(note.type)}</p>
                    <p>{note.preview}</p>
                    <Link to={`/knowledge?focus=${note.id}`} className="link-button">
                      Open note
                    </Link>
                  </article>
                ))}
              </div>
            ) : (
              <p className="muted">No notes found for this topic.</p>
            )}
          </article>

          <article className="card">
            <h3>Related Topics</h3>
            {data?.related_topics?.length ? (
              <div className="tag-list">
                {data.related_topics.map((relatedTopic) => (
                  <Link
                    key={relatedTopic}
                    to={`/topics/${encodeURIComponent(relatedTopic)}`}
                    className="tag tag-link"
                  >
                    {relatedTopic}
                  </Link>
                ))}
              </div>
            ) : (
              <p className="muted">No related topics found yet.</p>
            )}
          </article>
        </section>
      )}
    </div>
  );
}
