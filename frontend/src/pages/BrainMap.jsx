import { useEffect, useMemo, useRef, useState } from "react";
import ForceGraph2D from "react-force-graph-2d";
import { useNavigate } from "react-router-dom";
import api from "../api/client";

const GROUP_COLORS = {
  AI: "#3b82f6",
  Agriculture: "#22c55e",
  Math: "#a855f7",
  Mathematics: "#a855f7",
  Business: "#f97316",
  Knowledge: "#f97316",
  Spiritual: "#0891b2",
  General: "#9ca3af"
};

const DOMAIN_ANCHORS = {
  AI: { x: 0.22, y: 0.42 },
  Agriculture: { x: 0.52, y: 0.22 },
  Math: { x: 0.52, y: 0.82 },
  Mathematics: { x: 0.52, y: 0.82 },
  Business: { x: 0.8, y: 0.45 },
  Knowledge: { x: 0.36, y: 0.54 },
  Spiritual: { x: 0.78, y: 0.8 },
  General: { x: 0.64, y: 0.28 }
};

function hexToRgb(hex) {
  const normalized = hex.replace("#", "");
  const value = normalized.length === 3
    ? normalized.split("").map((char) => char + char).join("")
    : normalized;
  const integer = Number.parseInt(value, 16);
  return {
    r: (integer >> 16) & 255,
    g: (integer >> 8) & 255,
    b: integer & 255
  };
}

function graphColor(group, importance = 0, dimmed = false) {
  const base = GROUP_COLORS[group] || GROUP_COLORS.General;
  const { r, g, b } = hexToRgb(base);
  const alpha = dimmed ? 0.14 : importance > 8 ? 1 : importance > 4 ? 0.78 : 0.45;
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

function clusterDisplayLabel(group, leader) {
  if (group === "Business" && leader?.label && /property|real estate/i.test(leader.label)) {
    return "REAL ESTATE";
  }
  if (group === "Math" || group === "Mathematics") {
    return "MATHEMATICS";
  }
  return String(group || "General").toUpperCase();
}

function createClusterAnchors(groups, width, height) {
  const sortedGroups = [...groups].sort();
  return new Map(
    sortedGroups.map((group, index) => {
      const fallbackAngle = (2 * Math.PI * index) / Math.max(sortedGroups.length, 1) - Math.PI / 2;
      const fallback = {
        x: width / 2 + Math.min(width, height) * 0.22 * Math.cos(fallbackAngle),
        y: height / 2 + Math.min(width, height) * 0.22 * Math.sin(fallbackAngle)
      };
      const anchor = DOMAIN_ANCHORS[group]
        ? { x: width * DOMAIN_ANCHORS[group].x, y: height * DOMAIN_ANCHORS[group].y }
        : fallback;
      return [group, anchor];
    })
  );
}

function createClusterForce(axis, anchorMap, width, height) {
  let nodes = [];

  const force = (alpha) => {
    const strength = 0.3 * alpha;
    nodes.forEach((node) => {
      const anchor = anchorMap.get(node.group) || { x: width / 2, y: height / 2 };
      if (axis === "x") {
        node.vx += (anchor.x - node.x) * strength;
      } else {
        node.vy += (anchor.y - node.y) * strength;
      }
    });
  };

  force.initialize = (nextNodes) => {
    nodes = nextNodes || [];
  };

  return force;
}

function createLeaderForce(axis, leaderMap) {
  let nodes = [];

  const force = (alpha) => {
    const strength = 0.22 * alpha;
    nodes.forEach((node) => {
      const leader = leaderMap.get(node.group);
      if (!leader || leader.id === node.id) {
        return;
      }
      if (axis === "x") {
        node.vx += ((leader.x || 0) - node.x) * strength;
      } else {
        node.vy += ((leader.y || 0) - node.y) * strength;
      }
    });
  };

  force.initialize = (nextNodes) => {
    nodes = nextNodes || [];
  };

  return force;
}

function nodeRadius(node) {
  const importance = node.importance || 0;
  if (importance < 1) {
    return 2;
  }
  return Math.min(34, 4 + importance * 2);
}

export default function BrainMap() {
  const navigate = useNavigate();
  const fgRef = useRef(null);
  const shellRef = useRef(null);
  const didAutoFitRef = useRef(false);
  const lastSearchFocusRef = useRef("");
  const [graph, setGraph] = useState({ nodes: [], edges: [] });
  const [selectedNodeId, setSelectedNodeId] = useState(null);
  const [hoveredNodeId, setHoveredNodeId] = useState(null);
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  const [graphSize, setGraphSize] = useState({ width: 1200, height: 920 });

  useEffect(() => {
    api
      .get("/api/graph")
      .then((response) => setGraph(response.data))
      .catch((err) => setError(err.response?.data?.detail || "Unable to load the brain map."));
  }, []);

  useEffect(() => {
    const updateSize = () => {
      const nextWidth = Math.max(720, shellRef.current?.clientWidth || 1200);
      setGraphSize({ width: nextWidth, height: 920 });
    };

    updateSize();
    window.addEventListener("resize", updateSize);
    return () => window.removeEventListener("resize", updateSize);
  }, []);

  const graphWithDegree = useMemo(() => {
    const nodeDegree = {};
    graph.edges.forEach((edge) => {
      const sourceId = typeof edge.source === "object" ? edge.source.id : edge.source;
      const targetId = typeof edge.target === "object" ? edge.target.id : edge.target;
      nodeDegree[sourceId] = (nodeDegree[sourceId] || 0) + 1;
      nodeDegree[targetId] = (nodeDegree[targetId] || 0) + 1;
    });

    return {
      nodes: graph.nodes.map((node) => ({
        ...node,
        degree: nodeDegree[node.id] || 1
      })),
      edges: graph.edges.map((edge) => ({ ...edge }))
    };
  }, [graph]);

  const filteredData = useMemo(
    () => ({
      nodes: graphWithDegree.nodes.map((node) => ({ ...node })),
      links: graphWithDegree.edges.map((edge) => ({ ...edge }))
    }),
    [graphWithDegree]
  );

  const searchMatches = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) {
      return [];
    }

    return [...graphWithDegree.nodes]
      .filter((node) => node.label.toLowerCase().includes(query))
      .sort((left, right) => {
        const leftStarts = left.label.toLowerCase().startsWith(query) ? 1 : 0;
        const rightStarts = right.label.toLowerCase().startsWith(query) ? 1 : 0;
        if (leftStarts !== rightStarts) {
          return rightStarts - leftStarts;
        }
        return (right.degree || 0) - (left.degree || 0);
      })
      .slice(0, 6);
  }, [graphWithDegree.nodes, search]);

  const selectedNode = graphWithDegree.nodes.find((node) => node.id === selectedNodeId) || null;
  const selectedGroup = selectedNode?.group || null;
  const availableGroups = useMemo(() => {
    const groups = new Set(filteredData.nodes.map((node) => node.group));
    return Object.entries(GROUP_COLORS).map(([group, color]) => ({
      group,
      color,
      hasNodes: groups.has(group)
    }));
  }, [filteredData.nodes]);
  const clusterAnchors = useMemo(
    () => createClusterAnchors(new Set(filteredData.nodes.map((node) => node.group)), graphSize.width, graphSize.height),
    [filteredData.nodes, graphSize]
  );
  const groupLeaders = useMemo(() => {
    const leaders = new Map();
    filteredData.nodes.forEach((node) => {
      const existing = leaders.get(node.group);
      if (!existing || (node.importance || 0) > (existing.importance || 0)) {
        leaders.set(node.group, node);
      }
    });
    return leaders;
  }, [filteredData.nodes]);
  const focusContext = useMemo(() => {
    if (!selectedNodeId) {
      return { neighborIds: new Set(), connectedEdges: new Set(), connectedLabels: [] };
    }

    const neighborIds = new Set([selectedNodeId]);
    const connectedEdges = new Set();
    const connectedLabelSet = new Set();

    filteredData.links.forEach((edge) => {
      const sourceId = typeof edge.source === "object" ? edge.source.id : edge.source;
      const targetId = typeof edge.target === "object" ? edge.target.id : edge.target;
      const edgeKey = `${sourceId}->${targetId}`;
      if (sourceId === selectedNodeId) {
        neighborIds.add(targetId);
        connectedEdges.add(edgeKey);
        connectedLabelSet.add(targetId);
      } else if (targetId === selectedNodeId) {
        neighborIds.add(sourceId);
        connectedEdges.add(edgeKey);
        connectedLabelSet.add(sourceId);
      }
    });

    return { neighborIds, connectedEdges, connectedLabels: Array.from(connectedLabelSet) };
  }, [filteredData, selectedNodeId]);
  const clusterLabels = useMemo(
    () =>
      availableGroups
        .filter(({ hasNodes }) => hasNodes)
        .map(({ group, color }) => {
          const anchor = clusterAnchors.get(group) || { x: graphSize.width / 2, y: graphSize.height / 2 };
          const leader = groupLeaders.get(group) || null;
          return {
            group,
            color,
            label: clusterDisplayLabel(group, leader),
            x: anchor.x,
            y: Math.max(36, anchor.y - 74),
            leader
          };
        }),
    [availableGroups, clusterAnchors, graphSize, groupLeaders]
  );

  useEffect(() => {
    if (!fgRef.current || !filteredData.nodes.length) {
      return;
    }

    const graphApi = fgRef.current;
    didAutoFitRef.current = false;
    graphApi.d3Force("charge").strength(-900);
    graphApi.d3Force("link").distance((link) => Math.max(180, graphSize.width / 6) + (link.weight || 1) * 20);
    graphApi.d3Force("center").strength(0.3);
    graphApi.d3Force("cluster-x", createClusterForce("x", clusterAnchors, graphSize.width, graphSize.height));
    graphApi.d3Force("cluster-y", createClusterForce("y", clusterAnchors, graphSize.width, graphSize.height));
    graphApi.d3Force("leader-x", createLeaderForce("x", groupLeaders));
    graphApi.d3Force("leader-y", createLeaderForce("y", groupLeaders));
    graphApi.d3Force("collision", null);
    graphApi.d3ReheatSimulation();
  }, [filteredData, graphSize, clusterAnchors, groupLeaders]);

  const focusNode = (nodeId) => {
    setSelectedNodeId(nodeId);
    const targetNode = filteredData.nodes.find((node) => node.id === nodeId);
    if (targetNode && fgRef.current) {
      fgRef.current.centerAt(targetNode.x, targetNode.y, 500);
      fgRef.current.zoom(2.1, 500);
    }
  };

  const handleSearchSubmit = (event) => {
    event.preventDefault();
    if (!searchMatches.length) {
      return;
    }
    focusNode(searchMatches[0].id);
  };

  useEffect(() => {
    const query = search.trim().toLowerCase();
    if (!query) {
      lastSearchFocusRef.current = "";
      return;
    }
    if (!searchMatches.length) {
      return;
    }

    const nextFocusKey = `${query}:${searchMatches[0].id}`;
    if (lastSearchFocusRef.current === nextFocusKey) {
      return;
    }

    lastSearchFocusRef.current = nextFocusKey;
    focusNode(searchMatches[0].id);
  }, [search, searchMatches]);

  const focusGroup = (group) => {
    const candidate = [...filteredData.nodes]
      .filter((node) => node.group === group)
      .sort((left, right) => (right.importance || 0) - (left.importance || 0))[0];
    if (!candidate) {
      return;
    }
    focusNode(candidate.id);
  };

  const handleReset = () => {
    if (fgRef.current && filteredData.nodes.length) {
      setSelectedNodeId(null);
      setSearch("");
      lastSearchFocusRef.current = "";
      fgRef.current.zoomToFit(600, 40);
    }
  };

  return (
    <div className="stack">
      <section className="card">
        <h2>Brain Map</h2>
        <p className="muted">Explore how your saved knowledge topics connect.</p>
      </section>

      <section className="card">
        <div className="brain-map-toolbar">
          <form className="brain-map-search" onSubmit={handleSearchSubmit}>
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search and focus a topic"
            />
          </form>
          <button type="button" className="secondary-button" onClick={handleReset}>
            Reset View
          </button>
        </div>
        {!!searchMatches.length && (
          <div className="brain-map-search-results">
            {searchMatches.map((match) => (
              <button
                key={match.id}
                type="button"
                className="brain-map-search-result"
                onClick={() => focusNode(match.id)}
              >
                <span>{match.label}</span>
                <span className="muted">{match.group}</span>
              </button>
            ))}
          </div>
        )}
        <div className="brain-map-legend">
          {availableGroups.map(({ group, color, hasNodes }) => (
            <button
              key={group}
              type="button"
              className={`brain-map-legend-chip ${selectedGroup === group ? "active" : ""} ${!hasNodes ? "disabled" : ""}`}
              onClick={() => focusGroup(group)}
              title={hasNodes ? `Focus ${group}` : `No ${group} nodes in this view`}
              disabled={!hasNodes}
            >
              <span className="brain-map-legend-dot" style={{ backgroundColor: color }} />
              {group}
            </button>
          ))}
        </div>

        {error && <p className="error-text">{error}</p>}
        {!error && filteredData.nodes.length === 0 ? (
          <p className="muted">No graph data available yet. Add more topic-linked knowledge first.</p>
        ) : (
          <div ref={shellRef} className="brain-map-canvas force-graph-shell">
            <div className="brain-map-overlay">
              {clusterLabels.map((cluster) => (
                <button
                  key={cluster.group}
                  type="button"
                  className={`brain-map-cluster-label ${selectedGroup === cluster.group ? "active" : ""}`}
                  style={{
                    left: `${cluster.x}px`,
                    top: `${cluster.y}px`,
                    borderColor: cluster.color,
                    color: cluster.color
                  }}
                  onClick={() => focusGroup(cluster.group)}
                  title={cluster.leader ? `Focus ${cluster.label} around ${cluster.leader.label}` : `Focus ${cluster.label}`}
                >
                  <span
                    className="brain-map-cluster-dot"
                    style={{ backgroundColor: cluster.color }}
                  />
                  {cluster.label}
                </button>
              ))}
            </div>
            <ForceGraph2D
              ref={fgRef}
              width={graphSize.width}
              height={graphSize.height}
              graphData={filteredData}
              nodeRelSize={6}
              nodeVal={(node) => nodeRadius(node)}
              cooldownTicks={160}
              onEngineStop={() => {
                if (!didAutoFitRef.current && fgRef.current) {
                  fgRef.current.zoomToFit(700, 40);
                  didAutoFitRef.current = true;
                }
              }}
              linkWidth={(link) => {
                const baseWidth = 1 + (link.weight || 1);
                if (!selectedNodeId) {
                  return Math.min(6, baseWidth);
                }
                const sourceId = typeof link.source === "object" ? link.source.id : link.source;
                const targetId = typeof link.target === "object" ? link.target.id : link.target;
                const isConnected = sourceId === selectedNodeId || targetId === selectedNodeId;
                return isConnected ? Math.min(7, baseWidth + 0.8) : 0.8;
              }}
              linkColor={(link) => {
                if (!selectedNodeId) {
                  return "rgba(59, 130, 246, 0.38)";
                }
                const sourceId = typeof link.source === "object" ? link.source.id : link.source;
                const targetId = typeof link.target === "object" ? link.target.id : link.target;
                const isConnected = sourceId === selectedNodeId || targetId === selectedNodeId;
                return isConnected ? "rgba(37, 99, 235, 0.9)" : "rgba(148, 163, 184, 0.08)";
              }}
              nodeLabel={(node) => `${node.label} (${node.group || "General"})`}
              nodeColor={(node) => {
                if ((node.importance || 0) < 1) {
                  return "rgba(203, 213, 225, 0.12)";
                }
                if (!selectedNodeId) {
                  return graphColor(node.group, node.importance || 0, false);
                }
                return graphColor(node.group, node.importance || 0, !focusContext.neighborIds.has(node.id));
              }}
              enableNodeDrag={true}
              onNodeHover={(node) => setHoveredNodeId(node?.id || null)}
              onNodeClick={(node) => focusNode(node.id)}
              nodeCanvasObject={(node, ctx, globalScale) => {
                const label = node.label;
                const fontSize = Math.max(11, 15 / globalScale);
                const radius = nodeRadius(node);
                const isSelected = selectedNodeId === node.id;
                const isNeighbor = focusContext.neighborIds.has(node.id);
                const isDimmed = selectedNodeId && !isNeighbor;
                const showLabel = isSelected || hoveredNodeId === node.id || (node.importance || 0) >= 5;

                ctx.beginPath();
                ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI, false);
                ctx.globalAlpha = isDimmed ? 0.22 : 1;
                ctx.fillStyle = graphColor(node.group, node.importance || 0, false);
                ctx.fill();
                ctx.globalAlpha = 1;

                if (showLabel) {
                  ctx.font = `${fontSize}px Segoe UI`;
                  ctx.fillStyle = isDimmed ? "rgba(15, 23, 42, 0.35)" : "#0f172a";
                  ctx.textAlign = "center";
                  ctx.fillText(label, node.x, node.y + radius + fontSize + 2);
                }

                if (isSelected) {
                  ctx.beginPath();
                  ctx.arc(node.x, node.y, radius + 5, 0, 2 * Math.PI, false);
                  ctx.strokeStyle = "#f97316";
                  ctx.lineWidth = 3.5;
                  ctx.stroke();
                } else if (selectedNodeId && isNeighbor) {
                  ctx.beginPath();
                  ctx.arc(node.x, node.y, radius + 3, 0, 2 * Math.PI, false);
                  ctx.strokeStyle = "rgba(37, 99, 235, 0.58)";
                  ctx.lineWidth = 2;
                  ctx.stroke();
                }
              }}
            />
          </div>
        )}
      </section>

      <section className="card">
        <h3>Details</h3>
        {!selectedNode ? (
          <p className="muted">Click a topic node to inspect its related knowledge.</p>
        ) : (
          <div className="stack compact">
            <div className="brain-detail-header">
              <strong>{selectedNode.label}</strong>
              <span className="tag">{selectedNode.group}</span>
              <span className="tag">{selectedNode.type}</span>
            </div>
            <p className="muted">{selectedNode.linked_count} linked item(s)</p>
            {!!focusContext.connectedLabels.length && (
              <div>
                <p className="source-meta">Directly connected topics</p>
                <div className="tag-list">
                  {focusContext.connectedLabels.map((label) => (
                    <button
                      key={`${selectedNode.id}-${label}`}
                      type="button"
                      className="tag tag-button"
                      onClick={() => focusNode(label)}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {selectedNode.linked_titles?.length > 0 ? (
              <div>
                <p className="source-meta">Linked notes</p>
                <ul className="simple-list">
                  {selectedNode.linked_titles.map((title, index) => (
                    <li key={`${selectedNode.id}-${index}-${title}`}>{title}</li>
                  ))}
                </ul>
              </div>
            ) : (
              <p className="muted">No linked knowledge items.</p>
            )}
            <p className="source-meta">
              Suggested next step: {focusContext.connectedLabels[0] ? `Explore ${focusContext.connectedLabels[0]}` : "Open this topic to review its notes."}
            </p>
            <div className="brain-detail-actions">
              {selectedNode.type === "topic" && (
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => navigate(`/topics/${encodeURIComponent(selectedNode.label)}`)}
                >
                  Open Topic Page
                </button>
              )}
              {(selectedNode.type === "knowledge" || selectedNode.type === "note") && (
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => navigate(`/knowledge?focus=${encodeURIComponent(selectedNode.id)}`)}
                >
                  Open Note
                </button>
              )}
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
