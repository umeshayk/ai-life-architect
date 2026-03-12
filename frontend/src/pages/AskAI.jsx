import { useState } from "react";
import api from "../api/client";

const EXAMPLES = [
  "What do I know about mushroom farming?",
  "Summarize my notes about semantic search.",
  "Which saved items mention Jyotirlinga temples?"
];

const formatTypeLabel = (type) => type.charAt(0).toUpperCase() + type.slice(1);

export default function AskAI() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!question.trim()) {
      return;
    }
    setError("");
    setLoading(true);
    try {
      const response = await api.post("/api/ai/ask", { question, top_k: 5 });
      setResult(response.data);
    } catch (err) {
      setResult(null);
      setError(err.response?.data?.detail || "Unable to get a grounded answer right now.");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      event.currentTarget.form?.requestSubmit();
    }
  };

  return (
    <div className="stack">
      <section className="card">
        <h2>Ask Your Knowledge Base</h2>
        <p className="muted">Grounded by your saved knowledge.</p>
        <form onSubmit={handleSubmit} className="stack">
          <textarea
            rows="5"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={EXAMPLES.join("\n")}
          />
          <div className="tag-list">
            {EXAMPLES.map((example) => (
              <button
                key={example}
                type="button"
                className="pill-button"
                onClick={() => setQuestion(example)}
              >
                {example}
              </button>
            ))}
          </div>
          <button type="submit">{loading ? "Thinking..." : "Ask AI"}</button>
        </form>
        {error && <p className="error-text">{error}</p>}
      </section>
      {result && (
        <section className="card">
          <h3>Answer</h3>
          <p>{result.answer}</p>
          <h3>Sources</h3>
          {result.sources.length === 0 ? (
            <p className="muted">No sources found.</p>
          ) : (
            <div className="stack compact">
              {result.sources.map((source) => (
                <article key={source.id} className="result-item">
                  <div className="row-between">
                    <strong>{source.title}</strong>
                    <span className="source-meta">
                      {formatTypeLabel(source.type)} · {Math.round(source.similarity * 100)}%
                    </span>
                  </div>
                  <p>{source.summary || "No summary available."}</p>
                </article>
              ))}
            </div>
          )}
        </section>
      )}
    </div>
  );
}
