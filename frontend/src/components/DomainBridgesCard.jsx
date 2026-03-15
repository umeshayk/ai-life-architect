export default function DomainBridgesCard({
  bridges,
  loading,
  error,
  addingTopic,
  focusedTopic,
  collapsed = false,
  onToggle,
  onAddTopic,
}) {
  const collapsedSubtitle = bridges.length
    ? `${bridges.length} bridge${bridges.length === 1 ? "" : "s"}${focusedTopic ? ` for ${focusedTopic}` : " across your graph"}`
    : focusedTopic
      ? `Bridge suggestions for ${focusedTopic}`
      : "Cross-domain connector topics for your graph.";

  return (
    <section className="card brain-side-card domain-bridges-card">
      <button
        type="button"
        className="panel-toggle"
        onClick={onToggle}
        aria-expanded={!collapsed}
      >
        <span>
          <h3>Domain Bridges</h3>
          <p className="muted panel-toggle-subtitle">
            {collapsed
              ? collapsedSubtitle
              : "Topics that can connect two active domains in your knowledge graph."}
          </p>
        </span>
        <span className={`panel-toggle-chevron ${collapsed ? "collapsed" : ""}`} aria-hidden="true" />
      </button>

      {!collapsed && (
        <div className="stack compact">
          {loading ? <p className="muted">Finding bridge topics across your graph...</p> : null}
          {error ? <p className="error-text">{error}</p> : null}
          {!loading && !error && !bridges.length ? (
            <p className="muted">No bridge topics right now. As your graph spans more domains, this card will update.</p>
          ) : null}

          {!!bridges.length && (
            <div className="domain-bridges-list">
              {bridges.map((bridge) => (
                <div key={`${bridge.topic}-${bridge.domains.join('-')}`} className="domain-bridges-item">
                  <div className="domain-bridges-copy">
                    <strong className="next-best-topic-link">{bridge.topic}</strong>
                    <p className="muted domain-bridges-reason">{bridge.reason}</p>
                    <div className="tag-list domain-bridges-tags">
                      {bridge.domains.map((domain) => (
                        <span key={`${bridge.topic}-${domain}`} className="tag">{domain}</span>
                      ))}
                      <span className="tag">{Math.round((bridge.confidence || 0) * 100)}%</span>
                      <span className="tag">{bridge.source === 'ai' ? 'AI' : 'Rules'}</span>
                    </div>
                  </div>
                  <button
                    type="button"
                    className="knowledge-expansion-add"
                    disabled={addingTopic === bridge.topic}
                    onClick={() => onAddTopic?.(bridge)}
                  >
                    {addingTopic === bridge.topic ? 'Adding...' : '+ Add'}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
