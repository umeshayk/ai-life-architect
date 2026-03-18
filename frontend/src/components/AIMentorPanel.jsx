import { useState } from "react";
import api from "../api/client";

const QUICK_QUESTIONS = [
  "What should I learn next in AI?",
  "Why should I learn Vector Databases?",
  "What skills does Hybrid Search unlock?",
  "How close am I to completing AI Retrieval Engineer?",
  "What topics am I missing in Agriculture Automation?"
];

function buildFollowUpQuestions(response, currentQuestion) {
  const suggestions = [
    response?.recommended_topic ? `Why is ${response.recommended_topic} important?` : null,
    response?.skills_unlocked?.[0] ? `What skills does ${response.skills_unlocked[0]} unlock?` : null,
    response?.path_name ? `How close am I to completing ${response.path_name}?` : null,
    response?.path_name ? `What topics am I missing in ${response.path_name}?` : null,
  ].filter(Boolean);

  const normalizedCurrent = currentQuestion.trim().toLowerCase();
  const deduped = [];
  const seen = new Set();

  for (const suggestion of suggestions) {
    const normalized = suggestion.trim().toLowerCase();
    if (normalized === normalizedCurrent || seen.has(normalized)) {
      continue;
    }
    seen.add(normalized);
    deduped.push(suggestion);
  }

  return deduped.slice(0, 3);
}

function renderMentorStateIcon(state) {
  return <span className={`mentor-path-state-icon ${state}`} aria-hidden="true" />;
}

function sourceBadgeLabel(source, cached) {
  if (cached || source === "cache") {
    return "Cached";
  }
  if (source === "hybrid") {
    return "Hybrid";
  }
  if (source === "ai") {
    return "AI Generated";
  }
  if (source === "fallback") {
    return "Fallback";
  }
  return "Rule Based";
}

function sourceBadgeClass(source, cached) {
  if (cached || source === "cache") {
    return "cache";
  }
  if (source === "hybrid") {
    return "hybrid";
  }
  if (source === "ai") {
    return "ai";
  }
  if (source === "fallback") {
    return "fallback";
  }
  return "rules";
}

export default function AIMentorPanel({ onTopicClick, onTopicAction, collapsed = false, onToggle = null }) {
  const [question, setQuestion] = useState(QUICK_QUESTIONS[0]);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const normalizedQuestion = question.trim().toLowerCase();
  const isMissingTopicsQuestion = normalizedQuestion.includes("missing");
  const filteredMissingTopics = (response?.missing_topics || []).filter(
    (topic) => topic !== response?.recommended_topic
  );
  const followUpQuestions = buildFollowUpQuestions(response, question);

  const askMentor = async (nextQuestion = question, refresh = false) => {
    const trimmed = nextQuestion.trim();
    if (!trimmed) {
      return;
    }

    setQuestion(trimmed);
    setIsLoading(true);
    setError("");
    try {
      const result = await api.post("/api/mentor/ask", { question: trimmed, refresh });
      setResponse(result.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to reach the mentor right now.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <section className="card brain-side-card">
      <button
        type="button"
        className="panel-toggle"
        onClick={onToggle || undefined}
        aria-expanded={!collapsed}
      >
        <span>
          <h3>AI Mentor</h3>
          <p className="muted panel-toggle-subtitle">
            {collapsed
              ? response?.recommended_topic
                ? `Last topic: ${response.recommended_topic}`
                : "Ask what to learn next, why it matters, and what it unlocks."
              : "Ask about your next topic, why it matters, and what it unlocks."}
          </p>
        </span>
        <span className={`panel-toggle-chevron ${collapsed ? "collapsed" : ""}`} aria-hidden="true" />
      </button>

      {!collapsed && (
        <div className="stack compact">
          <div className="mentor-input-row">
            <input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask the mentor about your roadmap" />
            <button type="button" onClick={() => askMentor()} disabled={isLoading}>
              {isLoading ? "Thinking..." : "Ask"}
            </button>
          </div>

          <div className="mentor-quick-grid">
            {QUICK_QUESTIONS.filter((item) => item.trim().toLowerCase() !== question.trim().toLowerCase()).map((item) => (
              <button
                key={item}
                type="button"
                className="mentor-quick-chip"
                onClick={() => askMentor(item)}
              >
                {item}
              </button>
            ))}
          </div>

          {error && <p className="error-text">{error}</p>}

          {response && (
            <article className="result-item mentor-response-card">
              <div className="row-between">
                <p className="source-meta">Answer</p>
                <span className={`knowledge-expansion-source ${sourceBadgeClass(response.source, response.cached)}`}>
                  {sourceBadgeLabel(response.source, response.cached)}
                </span>
              </div>
              <div className="mentor-section first">
                <p className="mentor-answer">{response.answer}</p>
              </div>

              {response.path_name && (
                <div className="mentor-section">
                  <p className="source-meta">Path</p>
                  <p className="mentor-inline-copy">{response.path_name}</p>
                  {response.path_progress && (
                    <>
                      <div className="mentor-path-progress">
                        <div className="mentor-path-progress-fill" style={{ width: `${response.path_progress.progress_percent}%` }} />
                      </div>
                      <p className="source-meta">
                        {response.path_progress.covered_count} / {response.path_progress.total_count} completed ({response.path_progress.progress_percent}%)
                      </p>
                    </>
                  )}

                  {!!response.path_topics?.length && (
                    <div className="mentor-path-topic-list">
                      {response.path_topics.map((item) => (
                        <div key={item.topic} className={`mentor-path-topic-row ${item.state}`}>
                          {renderMentorStateIcon(item.state)}
                          <button
                            type="button"
                            className="link-button mentor-path-topic-button"
                            onClick={() => onTopicClick({ topic: item.topic })}
                          >
                            {item.topic}
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {response.why_it_matters && (
                <div className="mentor-section">
                  <p className="source-meta">Why it matters</p>
                  <p className="mentor-inline-copy">{response.why_it_matters}</p>
                </div>
              )}

              {!!response.skills_unlocked?.length && (
                <div className="mentor-section">
                  <p className="source-meta">Skills unlocked</p>
                  <div className="tag-list">
                    {response.skills_unlocked.map((skill) => (
                      <button key={skill} type="button" className="tag tag-button" onClick={() => onTopicClick({ topic: skill })}>
                        {skill}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {!!filteredMissingTopics.length && !isMissingTopicsQuestion && (
                <div className="mentor-section">
                  <p className="source-meta">Remaining topics</p>
                  <div className="tag-list">
                    {filteredMissingTopics.map((topic) => (
                      <button key={topic} type="button" className="tag tag-button" onClick={() => onTopicClick({ topic })}>
                        {topic}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {response.recommended_topic && response.recommended_action && (
                <div className="mentor-section mentor-recommendation-card">
                  <p className="mentor-recommendation-label">
                    <span className="mentor-target-icon" aria-hidden="true" />
                    <span>Recommended Next Topic</span>
                  </p>
                  <button
                    type="button"
                    className="link-button related-note-button mentor-topic-link"
                    onClick={() => onTopicClick({ topic: response.recommended_topic })}
                  >
                    {response.recommended_topic}
                  </button>
                  {(response.recommended_topic_reason || response.why_it_matters) && (
                    <div className="mentor-recommendation-why">
                      <p className="mentor-recommendation-subtitle">Why this topic?</p>
                      <p className="mentor-inline-copy">{response.recommended_topic_reason || response.why_it_matters}</p>
                    </div>
                  )}
                  <div className="mentor-recommendation-actions">
                    <button
                      type="button"
                      className={`suggestion-action-button ${response.recommended_action === "focus" ? "focus" : "add"}`}
                      onClick={() => onTopicAction({ topic: response.recommended_topic, action: response.recommended_action })}
                    >
                      <span className={`suggestion-action-icon ${response.recommended_action === "focus" ? "focus" : "add"}`} aria-hidden="true" />
                      <span>{response.recommended_action === "focus" ? "Focus Topic" : "Add Topic"}</span>
                    </button>
                    <button
                      type="button"
                      className="secondary-button"
                      onClick={() => askMentor(question, true)}
                      disabled={isLoading}
                    >
                      {isLoading ? "Refreshing..." : "Refresh AI"}
                    </button>
                  </div>
                </div>
              )}

              {!!followUpQuestions.length && (
                <div className="mentor-section mentor-follow-up-section">
                  <p className="source-meta">Follow-up Questions</p>
                  <div className="mentor-quick-grid">
                    {followUpQuestions.map((item) => (
                      <button
                        key={item}
                        type="button"
                        className="mentor-quick-chip"
                        onClick={() => askMentor(item)}
                      >
                        {item}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </article>
          )}
        </div>
      )}
    </section>
  );
}
