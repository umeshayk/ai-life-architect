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

function flattenReplayEvents(eventGroups) {
  return [...eventGroups]
    .flatMap((group) => group.events || [])
    .slice()
    .sort((left, right) => new Date(left.created_at).getTime() - new Date(right.created_at).getTime());
}

function replayEdgeKey(source, target) {
  return [source, target].sort().join("::");
}

function buildReplaySnapshot(events, activeIndex) {
  if (!events.length || activeIndex < 0) {
    return { nodes: [], edges: [] };
  }

  const visibleEvents = events.slice(0, activeIndex + 1);
  const nodeMap = new Map();
  const edgeMap = new Map();

  visibleEvents.forEach((event, index) => {
    if (event.topic && !nodeMap.has(event.topic)) {
      nodeMap.set(event.topic, {
        id: event.topic,
        label: event.topic,
        firstSeenIndex: index
      });
    }

    if (event.related_topic && !nodeMap.has(event.related_topic)) {
      nodeMap.set(event.related_topic, {
        id: event.related_topic,
        label: event.related_topic,
        firstSeenIndex: index
      });
    }

    if (event.topic && event.related_topic) {
      const edgeId = replayEdgeKey(event.topic, event.related_topic);
      if (!edgeMap.has(edgeId)) {
        edgeMap.set(edgeId, {
          id: edgeId,
          source: event.related_topic,
          target: event.topic,
          firstSeenIndex: index
        });
      }
    }
  });

  const orderedNodes = [...nodeMap.values()].sort((left, right) => left.firstSeenIndex - right.firstSeenIndex);
  const centerX = 480;
  const centerY = 220;
  const positionedNodes = orderedNodes.map((node, index) => {
    if (index === 0) {
      return { ...node, x: centerX, y: centerY, radius: 30 };
    }

    const ring = Math.floor((index - 1) / 6) + 1;
    const indexInRing = (index - 1) % 6;
    const itemsInRing = Math.min(6, orderedNodes.length - (ring - 1) * 6 - 1);
    const angle = (Math.PI * 2 * indexInRing) / Math.max(itemsInRing, 1) - Math.PI / 2;
    const radius = 95 + ring * 72;
    return {
      ...node,
      x: centerX + Math.cos(angle) * radius,
      y: centerY + Math.sin(angle) * radius,
      radius: 22
    };
  });

  const positionedNodeMap = new Map(positionedNodes.map((node) => [node.id, node]));
  const positionedEdges = [...edgeMap.values()]
    .map((edge) => ({
      ...edge,
      sourceNode: positionedNodeMap.get(edge.source),
      targetNode: positionedNodeMap.get(edge.target)
    }))
    .filter((edge) => edge.sourceNode && edge.targetNode);

  return { nodes: positionedNodes, edges: positionedEdges };
}

function replayEventSummary(event) {
  if (!event) {
    return "Start replay to see how your knowledge graph evolved.";
  }

  if (event.related_topic) {
    return `${event.topic} connected with ${event.related_topic} via ${event.event_label.toLowerCase()}.`;
  }

  if (typeof event.metadata?.mastery_score === "number") {
    return `${event.topic} mastery reached ${Math.round(event.metadata.mastery_score * 100)}%.`;
  }

  return `${event.topic || "Topic"}: ${event.event_label}.`;
}

function TimelinePanel({ title, subtitle, summary, open, onToggle, children, actions }) {
  const collapsedSubtitle = summary || subtitle;

  return (
    <section className="card">
      <button type="button" className="panel-toggle" onClick={onToggle}>
        <div>
          <h3>{title}</h3>
          <p className="muted panel-toggle-subtitle">{open ? subtitle : collapsedSubtitle}</p>
        </div>
        <span className={`panel-toggle-chevron ${open ? "" : "collapsed"}`} aria-hidden="true" />
      </button>
      {open ? (
        <div className="stack compact timeline-panel-body">
          {actions ? <div className="timeline-panel-actions">{actions}</div> : null}
          {children}
        </div>
      ) : null}
    </section>
  );
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
  const [isReplayPlaying, setIsReplayPlaying] = useState(false);
  const [replayIndex, setReplayIndex] = useState(0);
  const [openGroups, setOpenGroups] = useState({});
  const [openEventGroups, setOpenEventGroups] = useState({});
  const [openPanels, setOpenPanels] = useState({
    insight: false,
    forecast: false,
    weekly: false,
    evolution: false,
    topTopics: false,
    events: false,
    replay: false
  });

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
  const eventGroups = timeline?.event_groups || [];
  const topTopics = timeline?.top_topics || [];
  const hasItems = useMemo(() => groups.some((group) => group.count > 0), [groups]);
  const replayEvents = useMemo(() => flattenReplayEvents(eventGroups), [eventGroups]);
  const replaySnapshot = useMemo(
    () => buildReplaySnapshot(replayEvents, Math.min(replayIndex, replayEvents.length - 1)),
    [replayEvents, replayIndex]
  );
  const activeReplayEvent = replayEvents.length ? replayEvents[Math.min(replayIndex, replayEvents.length - 1)] : null;
  const chartWidth = 920;
  const chartHeight = 320;
  const chartPadding = { top: 24, right: 24, bottom: 48, left: 40 };
  const chartSeries = useMemo(
    () => buildChartPaths(evolution?.labels || [], evolution?.series || [], chartWidth, chartHeight, chartPadding),
    [evolution]
  );
  const togglePanel = (panelKey) => {
    setOpenPanels((current) => ({
      ...current,
      [panelKey]: !current[panelKey]
    }));
  };

  const toggleGroup = (groupKey) => {
    setOpenGroups((current) => ({
      ...current,
      [groupKey]: !current[groupKey]
    }));
  };

  const toggleEventGroup = (groupKey) => {
    setOpenEventGroups((current) => ({
      ...current,
      [groupKey]: !current[groupKey]
    }));
  };

  const yAxisTicks = useMemo(() => {
    const maxValue = Math.max(1, ...(evolution?.series || []).flatMap((entry) => entry.values));
    const tickCount = Math.min(4, maxValue);
    return Array.from({ length: tickCount + 1 }, (_, index) => Math.round((maxValue * index) / tickCount));
  }, [evolution]);

  useEffect(() => {
    setReplayIndex(0);
    setIsReplayPlaying(false);
  }, [eventGroups]);

  useEffect(() => {
    setOpenGroups((current) => {
      const next = {};
      groups.forEach((group) => {
        next[group.date_key] = Object.prototype.hasOwnProperty.call(current, group.date_key) ? current[group.date_key] : false;
      });

      const currentKeys = Object.keys(current);
      const nextKeys = Object.keys(next);
      const unchanged =
        currentKeys.length === nextKeys.length &&
        nextKeys.every((key) => current[key] === next[key]);

      return unchanged ? current : next;
    });
  }, [groups]);

  useEffect(() => {
    setOpenEventGroups((current) => {
      const next = {};
      eventGroups.forEach((group) => {
        next[group.date_key] = Object.prototype.hasOwnProperty.call(current, group.date_key) ? current[group.date_key] : false;
      });

      const currentKeys = Object.keys(current);
      const nextKeys = Object.keys(next);
      const unchanged =
        currentKeys.length === nextKeys.length &&
        nextKeys.every((key) => current[key] === next[key]);

      return unchanged ? current : next;
    });
  }, [eventGroups]);

  useEffect(() => {
    if (!isReplayPlaying || replayEvents.length <= 1) {
      return undefined;
    }

    const timer = window.setInterval(() => {
      setReplayIndex((current) => {
        if (current >= replayEvents.length - 1) {
          window.clearInterval(timer);
          setIsReplayPlaying(false);
          return current;
        }
        return current + 1;
      });
    }, 1100);

    return () => window.clearInterval(timer);
  }, [isReplayPlaying, replayEvents.length]);

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

      <TimelinePanel
        title="AI Insight Summary"
        subtitle="Patterns, momentum, gaps, and suggested directions from your recent activity."
        summary={insights?.dominant_topic ? `Dominant topic: ${insights.dominant_topic}` : "No insight summary yet."}
        open={openPanels.insight}
        onToggle={() => togglePanel("insight")}
      >
        <div className="timeline-insight-hero">
          <div className="timeline-insight-hero-copy">
            <span className="timeline-insight-eyebrow">Monthly Readout</span>
            <p className="timeline-insight-copy">{insights?.summary || "Not enough activity yet to generate insights."}</p>
          </div>
          <div className="timeline-insight-highlight-card">
            <span className="timeline-insight-highlight-label">Dominant Topic</span>
            <p className="timeline-insight-highlight-topic">{insights?.dominant_topic || "-"}</p>
            <p className="muted">Most active concept in your recent graph activity.</p>
          </div>
        </div>

        <div className="timeline-insight-strip">
          <div className="timeline-momentum-card highlight">
            <h4>Fastest Growing</h4>
            <p className="timeline-summary-value">{insights?.fastest_topic || "-"}</p>
          </div>
          <div className="timeline-momentum-card highlight">
            <h4>Emerging Focus</h4>
            <p className="timeline-summary-value">{insights?.emerging_topic || "-"}</p>
          </div>
          <div className="timeline-momentum-card highlight">
            <h4>Stable Theme</h4>
            <p className="timeline-summary-value">{insights?.stable_topic || "-"}</p>
          </div>
        </div>

        <div className="timeline-insight-grid refined">
          <div className="timeline-insight-section-card">
            <div className="row-between">
              <h4>Emerging Topics</h4>
              <span className="tag">{insights?.emerging_topics?.length || 0}</span>
            </div>
            {insights?.emerging_topics?.length ? (
              <div className="tag-list">
                {insights.emerging_topics.map((topic) => (
                  <Link key={topic} to={`/topics/${encodeURIComponent(topic)}`} className="tag tag-link">{topic}</Link>
                ))}
              </div>
            ) : (
              <p className="muted">No emerging topics detected yet.</p>
            )}
          </div>

          <div className="timeline-insight-section-card">
            <div className="row-between">
              <h4>Suggested Exploration</h4>
              <span className="tag">{insights?.suggested_topics?.length || 0}</span>
            </div>
            {insights?.suggested_topics?.length ? (
              <div className="tag-list">
                {insights.suggested_topics.map((topic) => (
                  <Link key={topic} to={`/topics/${encodeURIComponent(topic)}`} className="tag tag-link timeline-exploration-chip">{topic}</Link>
                ))}
              </div>
            ) : (
              <p className="muted">No exploration suggestions yet.</p>
            )}
          </div>

          <div className="timeline-insight-section-card">
            <div className="row-between">
              <h4>Knowledge Gaps</h4>
              <span className="tag">{insights?.knowledge_gaps?.length || 0}</span>
            </div>
            {insights?.knowledge_gaps?.length ? (
              <div className="tag-list">
                {insights.knowledge_gaps.map((topic) => (
                  <Link key={topic} to={`/topics/${encodeURIComponent(topic)}`} className="tag tag-link">{topic}</Link>
                ))}
              </div>
            ) : (
              <p className="muted">No obvious knowledge gaps detected yet.</p>
            )}
          </div>

          {!!insights?.suggestions?.length ? (
            <div className="timeline-insight-section-card">
              <div className="row-between">
                <h4>Suggestions</h4>
                <span className="tag">{insights.suggestions.length}</span>
              </div>
              <ul className="simple-list timeline-insight-suggestions">
                {insights.suggestions.map((suggestion) => (
                  <li key={suggestion}>{suggestion}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>

        <div className="timeline-insight-lower-grid">
          <div>
            <h4>Knowledge Strategy</h4>
            {insights?.strategies?.length ? (
              <div className="stack compact">
                {insights.strategies.map((strategy) => (
                  <div key={strategy.domain} className="timeline-strategy-card refined">
                    <div className="row-between">
                      <h5>{strategy.domain} Learning Path</h5>
                      <span className="tag">{strategy.path.length} steps</span>
                    </div>
                    <div className="timeline-strategy-list">
                      {strategy.path.map((step) => (
                        <div key={`${strategy.domain}-${step.topic}`} className="timeline-strategy-step">
                          <span className={`timeline-strategy-marker ${step.completed ? "completed" : "pending"}`} aria-hidden="true" />
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
                  <div key={project.name} className="timeline-project-card refined">
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
                        <Link
                          key={`${project.name}-${topic}`}
                          to={`/topics/${encodeURIComponent(topic)}`}
                          className="tag tag-link"
                        >
                          {topic}
                        </Link>
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
        </div>
      </TimelinePanel>

      <TimelinePanel
        title="Knowledge Forecast"
        subtitle="See where your current learning trajectory is likely to lead next."
        summary={insights?.forecast?.length ? `${insights.forecast.length} domain forecasts available` : "No forecast available yet."}
        open={openPanels.forecast}
        onToggle={() => togglePanel("forecast")}
      >
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
      </TimelinePanel>

      <TimelinePanel
        title="Weekly Action Plan"
        subtitle="Practical next steps based on your latest graph activity."
        summary={actionPlan.length ? `${actionPlan.length} suggested actions this week` : "No weekly plan available yet."}
        open={openPanels.weekly}
        onToggle={() => togglePanel("weekly")}
      >
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
      </TimelinePanel>

      <TimelinePanel
        title="Knowledge Evolution Graph"
        subtitle="See how your interests and knowledge topics changed over time."
        summary={chartSeries.length ? `${chartSeries.length} tracked topic lines` : "No evolution data available yet."}
        open={openPanels.evolution}
        onToggle={() => togglePanel("evolution")}
      >
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
      </TimelinePanel>

      <TimelinePanel
        title="Top Topics In This Period"
        subtitle="Your most active topics in the selected time window."
        summary={topTopics.length ? topTopics.slice(0, 3).map((topic) => topic.name).join(", ") : "No topics yet for this range."}
        open={openPanels.topTopics}
        onToggle={() => togglePanel("topTopics")}
      >
        <div className="tag-list">
          {topTopics.length ? (
            topTopics.map((topic) => (
              <Link key={topic.name} to={`/topics/${encodeURIComponent(topic.name)}`} className="tag tag-link">
                {topic.name} ({topic.count})
              </Link>
            ))
          ) : (
            <p className="muted">No topics yet for this range.</p>
          )}
        </div>
      </TimelinePanel>


      <TimelinePanel
        title="Knowledge Events"
        subtitle="Track how your topic graph evolves through creation, linking, expansion, path membership, and mastery updates."
        summary={eventGroups.length ? `${eventGroups.reduce((count, group) => count + group.count, 0)} events in this period` : "No knowledge events recorded in this period yet."}
        open={openPanels.events}
        onToggle={() => togglePanel("events")}
      >
        <p className="muted">Track how your topic graph evolves through creation, linking, expansion, path membership, and mastery updates.</p>
        {!eventGroups.length ? (
          <p className="muted">No knowledge events recorded in this period yet.</p>
        ) : (
          <div className="timeline-event-list stack compact">
            {eventGroups.map((group) => {
              const isOpen = openEventGroups[group.date_key] ?? false;
              return (
                <div key={group.date_key} className="timeline-event-group">
                  <button
                    type="button"
                    className="panel-toggle"
                    onClick={() => toggleEventGroup(group.date_key)}
                  >
                    <div>
                      <h4>{group.label}</h4>
                      <p className="muted panel-toggle-subtitle">
                        {isOpen ? group.date_key : `${group.date_key} - ${group.count} events`}
                      </p>
                    </div>
                    <div className="timeline-group-toggle-meta">
                      <span className="tag">{group.count} events</span>
                      <span className={`panel-toggle-chevron ${isOpen ? "" : "collapsed"}`} aria-hidden="true" />
                    </div>
                  </button>
                  {isOpen ? (
                    <div className="stack compact timeline-panel-body">
                      {group.events.map((event) => {
                        const primaryTopic = event.topic?.trim();
                        const primaryTopicHref = primaryTopic ? `/topics/${encodeURIComponent(primaryTopic)}` : null;
                        const relatedTopicHref = event.related_topic ? `/topics/${encodeURIComponent(event.related_topic)}` : null;
                        const EventContainer = primaryTopicHref ? Link : "article";
                        const eventContainerProps = primaryTopicHref
                          ? { to: primaryTopicHref, className: "timeline-event-row timeline-event-link" }
                          : { className: "timeline-event-row" };

                        return (
                          <EventContainer key={event.id} {...eventContainerProps}>
                            <div className="row-between">
                              <strong>{event.topic || "Topic"}</strong>
                              <span className="tag">{event.event_label}</span>
                            </div>
                            <p className="muted">
                              {event.related_topic ? `${event.topic} -> ${event.related_topic}` : event.event_label}
                            </p>
                            <p className="source-meta">Source: {event.source}</p>
                            {event.metadata?.path_name ? <p className="source-meta">Path: {event.metadata.path_name}</p> : null}
                            {typeof event.metadata?.mastery_score === "number" ? (
                              <p className="source-meta">Mastery: {Math.round(event.metadata.mastery_score * 100)}%</p>
                            ) : null}
                            {(primaryTopicHref || relatedTopicHref) ? (
                              <div className="tag-list timeline-event-topic-links">
                                {primaryTopicHref ? <span className="tag">Open {primaryTopic}</span> : null}
                                {relatedTopicHref ? (
                                  <Link
                                    to={relatedTopicHref}
                                    className="tag tag-link"
                                    onClick={(clickEvent) => clickEvent.stopPropagation()}
                                  >
                                    Related: {event.related_topic}
                                  </Link>
                                ) : null}
                              </div>
                            ) : null}
                          </EventContainer>
                        );
                      })}
                    </div>
                  ) : null}
                </div>
              );
            })}
          </div>
        )}
      </TimelinePanel>

      <TimelinePanel
        title="Replay Knowledge Graph"
        subtitle="Watch topics and connections appear in the order they entered your graph."
        summary={replayEvents.length ? `${replayEvents.length} replay steps available` : "No replay events available in this range yet."}
        open={openPanels.replay}
        onToggle={() => togglePanel("replay")}
        actions={
          !!replayEvents.length ? (
            <button
              type="button"
              className="secondary-button"
              onClick={(event) => {
                event.stopPropagation();
                if (!isReplayPlaying && replayIndex >= replayEvents.length - 1) {
                  setReplayIndex(0);
                }
                setIsReplayPlaying((current) => !current);
              }}
            >
              {isReplayPlaying ? "Pause" : replayIndex >= replayEvents.length - 1 ? "Replay" : "Play"}
            </button>
          ) : null
        }
      >
        {!replayEvents.length ? (
          <p className="muted">No replay events available in this range yet.</p>
        ) : (
          <div className="timeline-replay-shell stack compact">
            <div className="timeline-replay-controls">
              <div className="timeline-replay-range-row">
                <input
                  type="range"
                  min="0"
                  max={Math.max(replayEvents.length - 1, 0)}
                  value={Math.min(replayIndex, replayEvents.length - 1)}
                  onChange={(event) => {
                    setReplayIndex(Number(event.target.value));
                    setIsReplayPlaying(false);
                  }}
                />
                <span className="tag">
                  Step {Math.min(replayIndex + 1, replayEvents.length)} / {replayEvents.length}
                </span>
              </div>
              <div className="timeline-replay-summary">
                <strong>{activeReplayEvent?.event_label || "Ready"}</strong>
                <p className="muted">{replayEventSummary(activeReplayEvent)}</p>
                {activeReplayEvent ? (
                  <p className="source-meta">
                    {formatCreatedAt(activeReplayEvent.created_at)} | Source: {activeReplayEvent.source}
                  </p>
                ) : null}
              </div>
            </div>

            <div className="timeline-replay-stage">
              <svg viewBox="0 0 960 440" className="timeline-replay-graph" role="img" aria-label="Knowledge graph replay">
                {replaySnapshot.edges.map((edge) => (
                  <line
                    key={edge.id}
                    x1={edge.sourceNode.x}
                    y1={edge.sourceNode.y}
                    x2={edge.targetNode.x}
                    y2={edge.targetNode.y}
                    className="timeline-replay-edge"
                  />
                ))}
                {replaySnapshot.nodes.map((node, index) => (
                  <g key={node.id} transform={`translate(${node.x}, ${node.y})`}>
                    <circle
                      r={node.radius}
                      className={index === 0 ? "timeline-replay-node primary" : "timeline-replay-node"}
                    />
                    <text y={node.radius + 22} textAnchor="middle" className="timeline-replay-label">
                      {node.label}
                    </text>
                  </g>
                ))}
              </svg>
            </div>
          </div>
        )}
      </TimelinePanel>

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
          {groups.map((group) => {
            const isOpen = openGroups[group.date_key] ?? false;
            return (
              <section key={group.date_key} className="card timeline-group-card">
                <button
                  type="button"
                  className="panel-toggle"
                  onClick={() => toggleGroup(group.date_key)}
                >
                  <div>
                    <h3>{group.label}</h3>
                    <p className="muted panel-toggle-subtitle">
                      {isOpen ? group.date_key : `${group.date_key} - ${group.count} items`}
                    </p>
                  </div>
                  <div className="timeline-group-toggle-meta">
                    <span className="tag">{group.count} items</span>
                    <span className={`panel-toggle-chevron ${isOpen ? "" : "collapsed"}`} aria-hidden="true" />
                  </div>
                </button>

                {isOpen ? (
                  <div className="stack compact timeline-panel-body">
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
                              <Link key={`${item.id}-${topic}`} to={`/topics/${encodeURIComponent(topic)}`} className="tag tag-link">
                                {topic}
                              </Link>
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
                ) : null}
              </section>
            );
          })}
        </div>
      )}
    </div>
  );
}
