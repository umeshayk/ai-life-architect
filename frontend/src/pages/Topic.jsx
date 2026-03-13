import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import api from "../api/client";

function formatTypeLabel(type) {
  return type ? type.charAt(0).toUpperCase() + type.slice(1) : "Note";
}

export default function Topic() {
  const { topic } = useParams();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadTopic = async () => {
      setLoading(true);
      setError("");
      try {
        const response = await api.get(`/api/topics/${encodeURIComponent(topic)}`);
        setData(response.data);
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
