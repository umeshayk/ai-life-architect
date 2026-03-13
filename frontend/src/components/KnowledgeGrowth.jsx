export default function KnowledgeGrowth({ growth }) {
  if (!growth) {
    return null;
  }

  const maxNotes = Math.max(1, ...(growth.timeline || []).map((point) => point.notes));

  return (
    <section className="card">
      <h3>Knowledge Growth</h3>
      <div className="dashboard-grid">
        <div className="result-item">
          <h4>📚 Notes Saved</h4>
          <p className="metric">{growth.notes_count}</p>
        </div>
        <div className="result-item">
          <h4>🧠 Topics Discovered</h4>
          <p className="metric">{growth.topics_count}</p>
        </div>
        <div className="result-item">
          <h4>📈 Weekly Growth</h4>
          <p className="metric">+{growth.weekly_growth}</p>
        </div>
        <div className="result-item">
          <h4>🔥 Fastest Topic</h4>
          <p className="timeline-summary-value">{growth.fastest_topic || "-"}</p>
        </div>
      </div>
      <div className="stack compact">
        {(growth.timeline || []).map((point) => (
          <div key={point.month} className="growth-row">
            <div className="row-between">
              <strong>{point.month}</strong>
              <span className="source-meta">{point.notes} notes | {point.topics} topics</span>
            </div>
            <div className="growth-bar-track">
              <div
                className="growth-bar-fill"
                style={{ width: `${Math.max(8, Math.round((point.notes / maxNotes) * 100))}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
