import { useMemo, useState } from "react";
import api from "../api/client";

const EXAMPLES = [
  "What should I learn next in AI systems?",
  "Summarize what I know about mushroom farming.",
  "What are my current knowledge gaps?",
  "Which project is progressing fastest?",
  "What should I focus on this week?"
];

const formatTypeLabel = (type) => type.charAt(0).toUpperCase() + type.slice(1);
const SECTION_META = {
  1: { title: "Next Learning Step", icon: "🚀" },
  2: { title: "Knowledge Summary", icon: "📚" },
  3: { title: "Knowledge Gaps", icon: "⚠️" },
  4: { title: "Project Progress", icon: "📈" },
  5: { title: "Recommended Focus", icon: "🚀" },
  6: { title: "Additional Notes", icon: "📚" }
};

function parseAnswerSections(answer) {
  if (!answer) {
    return [];
  }

  const matches = [...answer.matchAll(/(?:^|\n)\s*(\d+)\.\s*([^\n]*)([\s\S]*?)(?=(?:\n\s*\d+\.\s)|$)/g)];
  if (!matches.length) {
    return [];
  }

  return matches.map((match, index) => {
    const sectionNumber = Number(match[1]);
    const rawContent = `${match[2] || ""}${match[3] || ""}`.trim();
    const meta = SECTION_META[sectionNumber] || {
      title: `Section ${index + 1}`,
      icon: "📚"
    };

    return {
      id: `${sectionNumber}-${index}`,
      title: meta.title,
      icon: meta.icon,
      content: rawContent
    };
  }).filter((section) => section.content);
}

function splitSectionItems(title, content) {
  const lines = content
    .split("\n")
    .map((line) => line.replace(/^[-*]\s*/, "").trim())
    .filter(Boolean);

  if (title === "Knowledge Gaps" && lines.length <= 1) {
    return content
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
  }

  if (lines.length > 1) {
    return lines;
  }

  return [];
}

export default function AskAI() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const answerSections = useMemo(() => parseAnswerSections(result?.answer || ""), [result]);

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
        <p className="muted">Ask about your knowledge, gaps, projects, and next steps.</p>
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
          {answerSections.length ? (
            <div className="dashboard-grid">
              {answerSections.map((section) => {
                const items = splitSectionItems(section.title, section.content);
                return (
                  <article key={section.id} className="result-item">
                    <h4>{section.icon} {section.title}</h4>
                    {items.length ? (
                      <ul className="simple-list">
                        {items.map((item, index) => (
                          <li key={`${section.id}-${index}-${item}`}>{item}</li>
                        ))}
                      </ul>
                    ) : (
                      <p>{section.content}</p>
                    )}
                  </article>
                );
              })}
            </div>
          ) : (
            <p>{result.answer}</p>
          )}
          {result.insights && (result.insights.dominant_topic || result.insights.next_step || result.insights.top_project) && (
            <div className="dashboard-grid">
              <div className="result-item">
                <h4>Dominant Topic</h4>
                <p className="timeline-summary-value">{result.insights.dominant_topic || "-"}</p>
              </div>
              <div className="result-item">
                <h4>Recommended Next Step</h4>
                <p className="timeline-summary-value">{result.insights.next_step || "-"}</p>
              </div>
              <div className="result-item">
                <h4>Top Project</h4>
                <p className="timeline-summary-value">
                  {result.insights.top_project || "-"}
                  {typeof result.insights.project_progress === "number" ? ` (${result.insights.project_progress}%)` : ""}
                </p>
              </div>
            </div>
          )}
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
                      {formatTypeLabel(source.type)} | {Math.round(source.similarity * 100)}%
                    </span>
                  </div>
                  <p>{source.summary || "No summary available."}</p>
                  {source.topic_names?.length > 0 && (
                    <div className="tag-list">
                      {source.topic_names.map((topicName) => (
                        <span key={`${source.id}-${topicName}`} className="tag">
                          {topicName}
                        </span>
                      ))}
                    </div>
                  )}
                </article>
              ))}
            </div>
          )}
        </section>
      )}
    </div>
  );
}
