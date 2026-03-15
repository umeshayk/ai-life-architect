export default function NextBestTopicCard({
  recommendations,
  loading,
  error,
  onTopicClick,
  onTopicAction,
  collapsed = false,
  onToggle,
}) {
  const topRecommendation = recommendations[0] || null;
  const moreRecommendations = recommendations.slice(1);

  const collapsedSubtitle = topRecommendation
    ? `${topRecommendation.topic} (${Math.round((topRecommendation.confidence || 0) * 100)}%)`
    : loading
      ? "Finding your next topic..."
      : "The strongest next step from your learning paths, gaps, and graph signals.";

  return (
    <section className="card brain-side-card next-best-topic-card">
      <button
        type="button"
        className="panel-toggle"
        onClick={onToggle}
        aria-expanded={!collapsed}
      >
        <span>
          <h3>Next Best Topic</h3>
          <p className="muted panel-toggle-subtitle">
            {collapsed
              ? collapsedSubtitle
              : "The strongest next step from your learning paths, gaps, and graph signals."}
          </p>
        </span>
        <span className={`panel-toggle-chevron ${collapsed ? "collapsed" : ""}`} aria-hidden="true" />
      </button>

      {!collapsed && (
        <>
          <div className="row-between next-best-topic-header">
            <div />
            {topRecommendation?.domain ? <span className="tag">{topRecommendation.domain}</span> : null}
          </div>

          {loading ? <p className="muted">Finding your next best topic...</p> : null}
          {error ? <p className="error-text">{error}</p> : null}
          {!loading && !error && !topRecommendation ? (
            <p className="muted">No recommendation yet. Keep growing your graph and this card will update.</p>
          ) : null}

          {topRecommendation ? (
            <div className="stack compact next-best-topic-body">
              <div>
                <button
                  type="button"
                  className="link-button next-best-topic-link"
                  onClick={() => onTopicClick?.(topRecommendation)}
                >
                  {topRecommendation.topic}
                </button>
                <p className="muted next-best-topic-reason">{topRecommendation.reason}</p>
              </div>

              <div className="row-between next-best-topic-meta-row">
                <span className="source-meta">Confidence: {Math.round((topRecommendation.confidence || 0) * 100)}%</span>
                {!!topRecommendation.path_name && <span className="source-meta">{topRecommendation.path_name}</span>}
              </div>

              {!!topRecommendation.source_signals?.length && (
                <div className="tag-list next-best-topic-signals">
                  {topRecommendation.source_signals.map((signal) => (
                    <span key={`${topRecommendation.topic}-${signal}`} className="tag">{signal.replaceAll("_", " ")}</span>
                  ))}
                </div>
              )}

              <div className="row-between next-best-topic-actions">
                <button
                  type="button"
                  className={`suggestion-action-button ${topRecommendation.action === "focus" ? "focus" : "add"}`}
                  onClick={() => onTopicAction?.(topRecommendation)}
                >
                  <span className={`suggestion-action-icon ${topRecommendation.action === "focus" ? "focus" : "add"}`} aria-hidden="true" />
                  <span>{topRecommendation.action === "focus" ? "Focus Topic" : "Add Topic"}</span>
                </button>
                {!!moreRecommendations.length && (
                  <span className="next-best-topic-more">{moreRecommendations.length} more recommendation{moreRecommendations.length === 1 ? "" : "s"}</span>
                )}
              </div>

              {!!moreRecommendations.length && (
                <div className="next-best-topic-more-list">
                  {moreRecommendations.map((recommendation) => (
                    <button
                      key={recommendation.topic}
                      type="button"
                      className="next-best-topic-mini"
                      onClick={() => onTopicClick?.(recommendation)}
                    >
                      <span className="next-best-topic-mini-copy">
                        <strong>{recommendation.topic}</strong>
                        <span className="muted">{recommendation.reason}</span>
                      </span>
                      <span className="next-best-topic-mini-score">{Math.round((recommendation.confidence || 0) * 100)}%</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          ) : null}
        </>
      )}
    </section>
  );
}
