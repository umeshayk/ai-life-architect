function DomainTopicIcon({ domain }) {
  const styleMap = {
    AI: { background: "#dbeafe", color: "#1d4ed8" },
    Agriculture: { background: "#dcfce7", color: "#15803d" },
    Bridge: { background: "#ccfbf1", color: "#0f766e" },
    Math: { background: "#f3e8ff", color: "#7e22ce" },
    Mathematics: { background: "#f3e8ff", color: "#7e22ce" },
    Business: { background: "#ffedd5", color: "#c2410c" },
    Knowledge: { background: "#ffedd5", color: "#ea580c" },
    Spiritual: { background: "#cffafe", color: "#0e7490" },
    General: { background: "#e2e8f0", color: "#475569" }
  };

  const style = styleMap[domain] || styleMap.General;

  if (domain === "AI") {
    return (
      <span className="domain-topic-icon" style={style} aria-hidden="true">
        <svg viewBox="0 0 16 16" className="domain-topic-svg">
          <rect x="3" y="4" width="10" height="8" rx="2" fill="none" stroke="currentColor" strokeWidth="1.6" />
          <path d="M6 2.5v2M10 2.5v2M5 7h.01M11 7h.01M6 10h4" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
        </svg>
      </span>
    );
  }

  if (domain === "Agriculture") {
    return (
      <span className="domain-topic-icon" style={style} aria-hidden="true">
        <svg viewBox="0 0 16 16" className="domain-topic-svg">
          <path d="M8 13V8" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
          <path d="M8 8c0-2.6 2-4.2 4.5-4.5-.3 2.5-1.9 4.5-4.5 4.5Z" fill="currentColor" opacity="0.9" />
          <path d="M8 9c0-2.1-1.6-3.4-3.8-3.7.2 2.1 1.6 3.7 3.8 3.7Z" fill="currentColor" opacity="0.65" />
          <path d="M5.5 13h5" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
        </svg>
      </span>
    );
  }

  if (domain === "Knowledge") {
    return (
      <span className="domain-topic-icon" style={style} aria-hidden="true">
        <svg viewBox="0 0 16 16" className="domain-topic-svg">
          <path d="M4 3.5h6.5A1.5 1.5 0 0 1 12 5v7H5.5A1.5 1.5 0 0 0 4 13.5v-10Z" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
          <path d="M4 12.5A1.5 1.5 0 0 1 5.5 11H12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      </span>
    );
  }

  if (domain === "Business") {
    return (
      <span className="domain-topic-icon" style={style} aria-hidden="true">
        <svg viewBox="0 0 16 16" className="domain-topic-svg">
          <rect x="3" y="5" width="10" height="7.5" rx="1.5" fill="none" stroke="currentColor" strokeWidth="1.5" />
          <path d="M6 5V4a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v1M3 8h10" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      </span>
    );
  }

  if (domain === "Math" || domain === "Mathematics") {
    return (
      <span className="domain-topic-icon" style={style} aria-hidden="true">
        <svg viewBox="0 0 16 16" className="domain-topic-svg">
          <rect x="4" y="2.5" width="8" height="11" rx="1.5" fill="none" stroke="currentColor" strokeWidth="1.5" />
          <path d="M6 5.5h4M6 8h4M6 10.5h4" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      </span>
    );
  }

  if (domain === "Spiritual") {
    return (
      <span className="domain-topic-icon" style={style} aria-hidden="true">
        <svg viewBox="0 0 16 16" className="domain-topic-svg">
          <path d="M8 2.5c1.8 2 2.7 3.3 2.7 4.7A2.7 2.7 0 1 1 5.3 7.2C5.3 5.8 6.2 4.5 8 2.5Z" fill="currentColor" opacity="0.85" />
          <path d="M8 9.5v3M6 12.5h4" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      </span>
    );
  }

  return (
    <span className="domain-topic-icon" style={style} aria-hidden="true">
      <svg viewBox="0 0 16 16" className="domain-topic-svg">
        <circle cx="8" cy="8" r="3.5" fill="currentColor" opacity="0.2" />
        <path d="M8 3.5v9M3.5 8h9" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
    </span>
  );
}

function TopicStateIcon({ state }) {
  if (state === "covered") {
    return (
      <span className={`learning-path-state-icon ${state}`} aria-hidden="true">
        <svg viewBox="0 0 16 16" className="learning-path-state-svg">
          <path d="M4 8.5 6.8 11.2 12 5.8" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </span>
    );
  }

  if (state === "started") {
    return (
      <span className={`learning-path-state-icon ${state}`} aria-hidden="true">
        <svg viewBox="0 0 16 16" className="learning-path-state-svg">
          <circle cx="8" cy="8" r="4.5" fill="none" stroke="currentColor" strokeWidth="1.7" opacity="0.45" />
          <path d="M8 3.5a4.5 4.5 0 0 1 4.5 4.5" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
          <circle cx="8" cy="8" r="1.3" fill="currentColor" />
        </svg>
      </span>
    );
  }

  return (
    <span className={`learning-path-state-icon ${state}`} aria-hidden="true">
      <svg viewBox="0 0 16 16" className="learning-path-state-svg">
        <circle cx="8" cy="8" r="4.6" fill="none" stroke="currentColor" strokeWidth="1.7" />
      </svg>
    </span>
  );
}

export default function LearningPathsPanel({
  learningPaths,
  error,
  onTopicClick,
  onTopicAction,
  collapsed = false,
  onToggle = null
}) {
  return (
    <section className="card brain-side-card">
      <button
        type="button"
        className="panel-toggle"
        onClick={onToggle || undefined}
        aria-expanded={!collapsed}
      >
        <span>
          <h3>Learning Paths</h3>
          <p className="muted panel-toggle-subtitle">
            {collapsed
              ? `${learningPaths.length} path${learningPaths.length === 1 ? "" : "s"} available`
              : "Track your progress through recommended learning paths."}
          </p>
        </span>
        <span className={`panel-toggle-chevron ${collapsed ? "collapsed" : ""}`} aria-hidden="true" />
      </button>
      {!collapsed && (
        <>
          {error && <p className="error-text">{error}</p>}
          {!error && learningPaths.length === 0 ? (
            <p className="muted">No learning paths are ready yet. Keep adding knowledge to build your roadmap.</p>
          ) : (
            <div className="stack compact">
              {learningPaths.map((path) => (
                <article key={path.path_name} className="result-item learning-path-card">
                  <div className="row-between learning-path-header">
                    <div>
                      <h4 className="learning-path-title">{path.path_name}</h4>
                      <p className="source-meta">Progress: {path.covered_count} / {path.total_count} completed</p>
                    </div>
                    <span className="tag">{path.domain}</span>
                  </div>

                  <div className="learning-path-progress">
                    <div className="learning-path-progress-fill" style={{ width: `${path.progress_percent}%` }} />
                  </div>
                  <p className="source-meta learning-path-percent">{path.progress_percent}% complete</p>

                  <div className="learning-path-topic-list">
                    {path.topics.map((topic) => {
                      const isNext = path.next_topic?.topic === topic.topic;
                      const topicTarget = { ...topic, domain: path.domain };
                      return (
                        <div key={`${path.path_name}-${topic.topic}`} className={`learning-path-topic-row ${topic.state} ${isNext ? "next" : ""}`}>
                          <TopicStateIcon state={topic.state} />
                          <button
                            type="button"
                            className="link-button learning-path-topic-button"
                            onClick={() => onTopicClick(topicTarget)}
                          >
                            {topic.topic}
                          </button>
                          {isNext && (
                            <button
                              type="button"
                              className="learning-path-next-chip"
                              onClick={() => onTopicClick(topicTarget)}
                            >
                              Next
                            </button>
                          )}
                        </div>
                      );
                    })}
                  </div>

                  {path.next_topic ? (
                    <div className="learning-path-next-block">
                      <p className="source-meta">Next topic</p>
                      <div className="row-between learning-path-next-row">
                        <button
                          type="button"
                          className="link-button related-note-button suggestion-topic-link"
                          onClick={() => onTopicClick(path.next_topic)}
                        >
                          <DomainTopicIcon domain={path.domain} />
                          <span>{path.next_topic.topic}</span>
                        </button>
                        <button
                          type="button"
                          className={`suggestion-action-button ${path.next_topic.action === "focus" ? "focus" : "add"}`}
                          onClick={() => onTopicAction(path.next_topic)}
                        >
                          <span className={`suggestion-action-icon ${path.next_topic.action === "focus" ? "focus" : "add"}`} aria-hidden="true" />
                          <span>{path.next_topic.action === "focus" ? "Focus Topic" : "Add Topic"}</span>
                        </button>
                      </div>
                    </div>
                  ) : (
                    <p className="success-text">Path completed.</p>
                  )}
                </article>
              ))}
            </div>
          )}
        </>
      )}
    </section>
  );
}
