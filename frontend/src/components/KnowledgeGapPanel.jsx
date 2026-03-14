export default function KnowledgeGapPanel({
  gaps,
  error,
  addingTopic,
  onAddTopic,
  onTopicClick,
  collapsed = false,
  onToggle = null,
}) {
  const totalGapCount = gaps.reduce((sum, path) => sum + (path.missing_topics?.length || 0), 0);

  return (
    <section className="card brain-side-card">
      <button
        type="button"
        className="panel-toggle"
        onClick={onToggle || undefined}
        aria-expanded={!collapsed}
      >
        <span>
          <h3>Knowledge Gaps</h3>
          <p className="muted panel-toggle-subtitle">
            {collapsed
              ? `${totalGapCount} gap${totalGapCount === 1 ? "" : "s"} across ${gaps.length} learning path${gaps.length === 1 ? "" : "s"}`
              : "See which topics are still missing in each learning path and add them into your graph."}
          </p>
        </span>
        <span className={`panel-toggle-chevron ${collapsed ? "collapsed" : ""}`} aria-hidden="true" />
      </button>

      {!collapsed && (
        <>
          {error && <p className="error-text">{error}</p>}
          {!error && gaps.length === 0 ? (
            <p className="muted">No major knowledge gaps right now. Keep expanding your graph to surface the next ones.</p>
          ) : (
            <div className="stack compact">
              {gaps.map((path) => (
                <article key={path.path_name} className="result-item knowledge-gap-card">
                  <div className="row-between learning-path-header">
                    <div>
                      <h4 className="learning-path-title">{path.path_name}</h4>
                      <p className="source-meta">Progress: {path.covered_count} / {path.total_count} completed</p>
                    </div>
                    <div className="knowledge-gap-header-meta">
                      <span className="tag">{path.domain}</span>
                      <span className={`knowledge-expansion-source ${path.cached ? "cache" : path.source === "hybrid" ? "hybrid" : path.source === "ai" ? "ai" : "rules"}`}>
                        {path.cached ? "Cached" : path.source === "hybrid" ? "Hybrid" : path.source === "ai" ? "AI" : "Rules"}
                      </span>
                    </div>
                  </div>

                  <div className="learning-path-progress">
                    <div className="learning-path-progress-fill" style={{ width: `${path.progress_percent}%` }} />
                  </div>
                  <p className="source-meta learning-path-percent">{path.progress_percent}% complete</p>

                  <div className="knowledge-gap-topic-list">
                    {path.missing_topics.map((topic) => (
                      <div key={`${path.path_name}-${topic.topic}`} className="knowledge-gap-topic-row">
                        <div className="knowledge-gap-topic-copy">
                          <strong>{topic.topic}</strong>
                          <p className="muted">{topic.reason}</p>
                        </div>
                        <button
                          type="button"
                          className="knowledge-expansion-add"
                          disabled={topic.action === "add" && addingTopic === topic.topic}
                          onClick={() => topic.action === "focus" ? onTopicClick?.({ topic: topic.topic, domain: path.domain }) : onAddTopic(topic.topic)}
                        >
                          {topic.action === "focus"
                            ? "Focus Topic"
                            : addingTopic === topic.topic
                              ? "Adding..."
                              : "+ Add"}
                        </button>
                      </div>
                    ))}
                  </div>
                </article>
              ))}
            </div>
          )}
        </>
      )}
    </section>
  );
}
