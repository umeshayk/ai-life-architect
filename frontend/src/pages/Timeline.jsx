import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import api from "../api/client";

const RANGE_OPTIONS = [
  { value: "7d", label: "Last 7 days" },
  { value: "30d", label: "Last 30 days" },
  { value: "all", label: "All time" }
];

const GROUP_OPTIONS = [
  { value: "day", label: "Day" },
  { value: "week", label: "Week" },
  { value: "month", label: "Month" }
];

const EVOLUTION_COLORS = ["#2563eb", "#0f766e", "#dc2626", "#7c3aed", "#ea580c", "#0891b2", "#65a30d", "#334155"];

function formatCreatedAt(value) {
  return new Date(value).toLocaleString([], {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit"
  });
}

function typeLabel(value) {
  if (value === "file") return "File";
  if (value === "link") return "Link";
  return "Note";
}

function buildChartPaths(labels, series, width, height, padding) {
  if (!labels.length || !series.length) {
    return [];
  }

  const maxValue = Math.max(1, ...series.flatMap((entry) => entry.values));
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  return series.map((entry, index) => {
    const points = entry.values.map((value, valueIndex) => {
      const x =
        labels.length === 1
          ? padding.left + chartWidth / 2
          : padding.left + (chartWidth * valueIndex) / (labels.length - 1);
      const y = padding.top + chartHeight - (value / maxValue) * chartHeight;
      return { x, y, value };
    });

    const path = points
      .map((point, pointIndex) => `${pointIndex === 0 ? "M" : "L"} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`)
      .join(" ");

    return {
      topic: entry.topic,
      color: EVOLUTION_COLORS[index % EVOLUTION_COLORS.length],
      points,
      path
    };
  });
}

function shouldRenderAxisLabel(index, totalLabels, groupBy) {
  if (totalLabels <= 10) {
    return true;
  }

  const step = groupBy === "day"
    ? Math.ceil(totalLabels / 8)
    : Math.ceil(totalLabels / 10);

  return index === 0 || index === totalLabels - 1 || index % step === 0;
}

export default function Timeline() {
  const [range, setRange] = useState("30d");
  const [groupBy, setGroupBy] = useState("week");
  const [timeline, setTimeline] = useState(null);
  const [evolution, setEvolution] = useState(null);
  const [actionPlan, setActionPlan] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [hoveredPoint, setHoveredPoint] = useState(null);

  const loadTimeline = async (nextRange = range, nextGroupBy = groupBy) => {
    setLoading(true);
    setError("");
    try {
      const [timelineResponse, evolutionResponse, actionPlanResponse] = await Promise.all([
        api.get("/api/timeline", {
          params: { range: nextRange, group_by: nextGroupBy }
        }),
        api.get("/api/timeline/evolution", {
          params: { range: nextRange, group_by: nextGroupBy, limit_topics: 5 }
        }),
        api.get("/api/timeline/action-plan", {
          params: { range: nextRange, group_by: nextGroupBy }
        })
      ]);
      setTimeline(timelineResponse.data);
      setEvolution(evolutionResponse.data);
      setActionPlan(actionPlanResponse.data.weekly_plan || []);
    } catch {
      setError("Unable to load the memory timeline right now.");
      setTimeline(null);
      setEvolution(null);
      setActionPlan([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTimeline();
  }, [range, groupBy]);

  const summary = timeline?.summary;
  const insights = timeline?.insights;
  const groups = timeline?.groups || [];
  const topTopics = timeline?.top_topics || [];
  const hasItems = useMemo(() => groups.some((group) => group.count > 0), [groups]);
  const chartWidth = 920;
  const chartHeight = 320;
  const chartPadding = { top: 24, right: 24, bottom: 48, left: 40 };
  const chartSeries = useMemo(
    () => buildChartPaths(evolution?.labels || [], evolution?.series || [], chartWidth, chartHeight, chartPadding),
    [evolution]
  );
  const yAxisTicks = useMemo(() => {
    const maxValue = Math.max(1, ...(evolution?.series || []).flatMap((entry) => entry.values));
    const tickCount = Math.min(4, maxValue);
    return Array.from({ length: tickCount + 1 }, (_, index) => Math.round((maxValue * index) / tickCount));
  }, [evolution]);

  return (
    <div className="stack">
      <section className="card">
        <h2>Memory Timeline</h2>
        <p className="muted">Explore how your saved knowledge has evolved over time.</p>
      </section>

      <section className="card timeline-controls">
        <div>
          <label htmlFor="timeline-range">Range</label>
          <select id="timeline-range" value={range} onChange={(event) => setRange(event.target.value)}>
            {RANGE_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="timeline-group-by">Group By</label>
          <select id="timeline-group-by" value={groupBy} onChange={(event) => setGroupBy(event.target.value)}>
            {GROUP_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
        </div>
      </section>

      <section className="card dashboard-grid">
        <div>
          <h3>Total Items</h3>
          <p className="metric">{summary?.total_items ?? "-"}</p>
        </div>
        <div>
          <h3>Most Active Period</h3>
          <p className="timeline-summary-value">{summary?.most_active_period ?? "-"}</p>
        </div>
        <div>
          <h3>Top Topics</h3>
          <p className="timeline-summary-value">{summary?.top_topics?.join(", ") || "-"}</p>
        </div>
        <div>
          <h3>Latest Saved</h3>
          <p className="timeline-summary-value">{summary?.latest_item_title || "-"}</p>
        </div>
      </section>

      <section className="card">
        <h3>AI Insight Summary</h3>
        <p className="timeline-insight-copy">{insights?.summary || "Not enough activity yet to generate insights."}</p>
        <div className="timeline-insight-grid">
          <div>
            <h4>Dominant Topic</h4>
            <p className="timeline-summary-value">{insights?.dominant_topic || "-"}</p>
          </div>
          <div>
            <h4>Emerging Topics</h4>
            {insights?.emerging_topics?.length ? (
              <div className="tag-list">
                {insights.emerging_topics.map((topic) => (
                  <span key={topic} className="tag">{topic}</span>
                ))}
              </div>
            ) : (
              <p className="muted">No emerging topics detected yet.</p>
            )}
          </div>
        </div>
        <div className="timeline-momentum-grid">
          <div className="timeline-momentum-card">
            <h4>Fastest Growing Topic</h4>
            <p className="timeline-summary-value">{insights?.fastest_topic || "-"}</p>
          </div>
          <div className="timeline-momentum-card">
            <h4>Emerging Topic</h4>
            <p className="timeline-summary-value">{insights?.emerging_topic || "-"}</p>
          </div>
          <div className="timeline-momentum-card">
            <h4>Stable Topic</h4>
            <p className="timeline-summary-value">{insights?.stable_topic || "-"}</p>
          </div>
        </div>
        <div>
          <h4>Suggested Exploration</h4>
          {insights?.suggested_topics?.length ? (
            <div className="tag-list">
              {insights.suggested_topics.map((topic) => (
                <button key={topic} type="button" className="pill-button">{topic}</button>
              ))}
            </div>
          ) : (
            <p className="muted">No exploration suggestions yet.</p>
          )}
        </div>
        <div>
          <h4>Knowledge Gaps</h4>
          {insights?.knowledge_gaps?.length ? (
            <div className="tag-list">
              {insights.knowledge_gaps.map((topic) => (
                <span key={topic} className="tag">{topic}</span>
              ))}
            </div>
          ) : (
            <p className="muted">No obvious knowledge gaps detected yet.</p>
          )}
        </div>
        <div>
          <h4>Knowledge Strategy</h4>
          {insights?.strategies?.length ? (
            <div className="stack compact">
              {insights.strategies.map((strategy) => (
                <div key={strategy.domain} className="timeline-strategy-card">
                  <h5>{strategy.domain} Learning Path</h5>
                  <div className="timeline-strategy-list">
                    {strategy.path.map((step) => (
                      <div key={`${strategy.domain}-${step.topic}`} className="timeline-strategy-step">
                        <span className={`timeline-strategy-marker ${step.completed ? "completed" : ""}`}>
                          {step.completed ? "✓" : "→"}
                        </span>
                        <span className={step.completed ? "timeline-strategy-complete" : ""}>{step.topic}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="muted">No strategy path available yet.</p>
          )}
        </div>
        <div>
          <h4>Active Knowledge Projects</h4>
          {insights?.projects?.length ? (
            <div className="stack compact">
              {insights.projects.map((project) => (
                <div key={project.name} className="timeline-project-card">
                  <div className="row-between">
                    <h5>{project.name}</h5>
                    <span className="tag">{Math.round(project.progress * 100)}%</span>
                  </div>
                  <div className="timeline-project-progress">
                    <div
                      className="timeline-project-progress-bar"
                      style={{ width: `${Math.max(8, Math.round(project.progress * 100))}%` }}
                    />
                  </div>
                  <div className="tag-list">
                    {project.topics.map((topic) => (
                      <span key={`${project.name}-${topic}`} className="tag">{topic}</span>
                    ))}
                  </div>
                  <p className="source-meta">Next suggested step: {project.next_step || "Project is well covered"}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="muted">No active knowledge projects detected yet.</p>
          )}
        </div>
        {!!insights?.suggestions?.length && (
          <>
            <h4>Suggestions</h4>
            <ul className="simple-list">
              {insights.suggestions.map((suggestion) => (
                <li key={suggestion}>{suggestion}</li>
              ))}
            </ul>
          </>
        )}
      </section>

      <section className="card">
        <h3>Knowledge Forecast</h3>
        {insights?.forecast?.length ? (
          <div className="stack compact">
            {insights.forecast.map((entry) => (
              <div key={entry.domain} className="timeline-forecast-card">
                <h4>{entry.domain} Expertise</h4>
                <p className="timeline-summary-value">Confidence: {Math.round(entry.confidence * 100)}%</p>
                <p className="source-meta">Estimated mastery: {entry.estimated_mastery_months} months</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="muted">No forecast available yet.</p>
        )}
      </section>

      <section className="card">
        <h3>Weekly Action Plan</h3>
        {actionPlan.length ? (
          <div className="stack compact">
            {actionPlan.map((item) => (
              <div key={`${item.domain}-${item.action}`} className="timeline-action-plan-card">
                <h4>{item.domain}</h4>
                <p className="timeline-summary-value">{item.action}</p>
                <p className="source-meta">{item.reason}</p>
                <Link
                  to={`/knowledge?topic=${encodeURIComponent(item.action.replace(/^(Study|Start)\s+/i, "").trim())}`}
                  className="action-btn"
                >
                  {item.action}
                </Link>
              </div>
            ))}
          </div>
        ) : (
          <p className="muted">No weekly plan available yet.</p>
        )}
      </section>

      <section className="card">
        <h3>Knowledge Evolution Graph</h3>
        <p className="muted">See how your interests and knowledge topics changed over time.</p>
        {!evolution?.labels?.length || !chartSeries.length ? (
          <p className="muted">No evolution data available for this range yet.</p>
        ) : (
          <div className="timeline-chart-shell">
            <div className="timeline-chart-legend">
              {chartSeries.map((entry) => (
                <span key={entry.topic} className="timeline-legend-item">
                  <span className="timeline-legend-swatch" style={{ backgroundColor: entry.color }} />
                  {entry.topic}
                </span>
              ))}
            </div>
            <div className="timeline-chart-wrap">
              <svg
                className="timeline-chart"
                viewBox={`0 0 ${chartWidth} ${chartHeight}`}
                role="img"
                aria-label="Knowledge evolution graph"
              >
                {yAxisTicks.map((tick) => {
                  const maxValue = Math.max(1, ...(evolution?.series || []).flatMap((entry) => entry.values));
                  const y =
                    chartPadding.top +
                    (chartHeight - chartPadding.top - chartPadding.bottom) -
                    (tick / maxValue) * (chartHeight - chartPadding.top - chartPadding.bottom);
                  return (
                    <g key={`tick-${tick}`}>
                      <line
                        x1={chartPadding.left}
                        y1={y}
                        x2={chartWidth - chartPadding.right}
                        y2={y}
                        className="timeline-grid-line"
                      />
                      <text x={chartPadding.left - 10} y={y + 4} className="timeline-axis-label timeline-axis-label-y">
                        {tick}
                      </text>
                    </g>
                  );
                })}
                {evolution.labels.map((label, index) => {
                  if (!shouldRenderAxisLabel(index, evolution.labels.length, groupBy)) {
                    return null;
                  }
                  const x =
                    evolution.labels.length === 1
                      ? chartPadding.left + (chartWidth - chartPadding.left - chartPadding.right) / 2
                      : chartPadding.left +
                        ((chartWidth - chartPadding.left - chartPadding.right) * index) / (evolution.labels.length - 1);
                  return (
                    <text
                      key={label}
                      x={x}
                      y={chartHeight - 16}
                      textAnchor="middle"
                      className="timeline-axis-label"
                    >
                      {label}
                    </text>
                  );
                })}
                {chartSeries.map((entry) => (
                  <g key={entry.topic}>
                    <path d={entry.path} fill="none" stroke={entry.color} strokeWidth="3" strokeLinecap="round" />
                    {entry.points.map((point, index) => (
                      <circle
                        key={`${entry.topic}-${index}`}
                        cx={point.x}
                        cy={point.y}
                        r="5"
                        fill={entry.color}
                        className="timeline-chart-point"
                        onMouseEnter={() =>
                          setHoveredPoint({
                            topic: entry.topic,
                            label: evolution.labels[index],
                            value: point.value,
                            x: point.x,
                            y: point.y
                          })
                        }
                        onMouseLeave={() => setHoveredPoint(null)}
                      />
                    ))}
                  </g>
                ))}
                {hoveredPoint && (
                  <g transform={`translate(${Math.min(hoveredPoint.x + 12, chartWidth - 170)}, ${Math.max(hoveredPoint.y - 54, 16)})`}>
                    <rect width="156" height="44" rx="10" className="timeline-tooltip-box" />
                    <text x="10" y="18" className="timeline-tooltip-text">{hoveredPoint.topic}</text>
                    <text x="10" y="34" className="timeline-tooltip-subtext">
                      {hoveredPoint.label}: {hoveredPoint.value}
                    </text>
                  </g>
                )}
              </svg>
            </div>
          </div>
        )}
      </section>

      <section className="card">
        <h3>Top Topics in This Period</h3>
        <div className="tag-list">
          {topTopics.length ? (
            topTopics.map((topic) => (
              <span key={topic.name} className="tag">
                {topic.name} ({topic.count})
              </span>
            ))
          ) : (
            <p className="muted">No topics yet for this range.</p>
          )}
        </div>
      </section>

      {loading ? (
        <section className="card">
          <p>Loading timeline...</p>
        </section>
      ) : error ? (
        <section className="card">
          <p className="error-text">{error}</p>
        </section>
      ) : !hasItems ? (
        <section className="card">
          <p className="muted">No saved knowledge in this period yet.</p>
        </section>
      ) : (
        <div className="timeline-list">
          {groups.map((group) => (
            <section key={group.date_key} className="card timeline-group-card">
              <div className="row-between">
                <div>
                  <h3>{group.label}</h3>
                  <p className="muted">{group.date_key}</p>
                </div>
                <span className="tag">{group.count} items</span>
              </div>

              <div className="stack compact">
                {group.items.map((item) => (
                  <article key={item.id} className="result-item timeline-item">
                    <div className="row-between timeline-item-header">
                      <div>
                        <h4 className="timeline-item-title">
                          <Link to={`/knowledge?focus=${item.id}`} className="link-button">
                            {item.title}
                          </Link>
                        </h4>
                        <p className="source-meta">
                          {typeLabel(item.type)} | {formatCreatedAt(item.created_at)}
                        </p>
                      </div>
                      <span className="tag">{typeLabel(item.type)}</span>
                    </div>

                    {item.summary && <p>{item.summary}</p>}

                    {!!item.topics.length && (
                      <div className="tag-list">
                        {item.topics.map((topic) => (
                          <span key={`${item.id}-${topic}`} className="tag">{topic}</span>
                        ))}
                      </div>
                    )}

                    {!!item.tags.length && (
                      <div className="tag-list">
                        {item.tags.map((tag) => (
                          <span key={`${item.id}-${tag}`} className="tag">{tag}</span>
                        ))}
                      </div>
                    )}
                  </article>
                ))}
              </div>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}
