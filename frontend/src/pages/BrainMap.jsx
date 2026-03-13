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

function graphColor(group) {
  return GROUP_COLORS[group] || GROUP_COLORS.General;
}

function nodeRadius(node) {
  return Math.min(28, 4 + (node.degree || 0) * 2);
}

export default function BrainMap() {
  const navigate = useNavigate();
  const fgRef = useRef(null);
  const shellRef = useRef(null);
  const didAutoFitRef = useRef(false);
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

  const filteredData = useMemo(() => {
    const query = search.trim().toLowerCase();
    const nodes = query
      ? graphWithDegree.nodes.filter((node) => node.label.toLowerCase().includes(query))
      : graphWithDegree.nodes;
    const nodeIds = new Set(nodes.map((node) => node.id));
    const links = graphWithDegree.edges
      .filter((edge) => {
        const sourceId = typeof edge.source === "object" ? edge.source.id : edge.source;
        const targetId = typeof edge.target === "object" ? edge.target.id : edge.target;
        return nodeIds.has(sourceId) && nodeIds.has(targetId);
      })
      .map((edge) => ({ ...edge }));
    return {
      nodes: nodes.map((node) => ({ ...node })),
      links
    };
  }, [graphWithDegree, search]);

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

  useEffect(() => {
    if (!fgRef.current || !filteredData.nodes.length) {
      return;
    }

    const graphApi = fgRef.current;
    didAutoFitRef.current = false;
    graphApi.d3Force("charge").strength(-900);
    graphApi.d3Force("link").distance((link) => Math.max(180, graphSize.width / 6) + (link.weight || 1) * 20);
    graphApi.d3Force("center").strength(0.3);
    graphApi.d3Force("collision", null);
    graphApi.d3ReheatSimulation();
  }, [filteredData, graphSize]);

  const focusNode = (nodeId) => {
    setSelectedNodeId(nodeId);
    const targetNode = filteredData.nodes.find((node) => node.id === nodeId);
    if (targetNode && fgRef.current) {
      fgRef.current.centerAt(targetNode.x, targetNode.y, 500);
      fgRef.current.zoom(2.1, 500);
    }
  };

  const focusGroup = (group) => {
    const candidate = [...filteredData.nodes]
      .filter((node) => node.group === group)
      .sort((left, right) => (right.degree || 0) - (left.degree || 0))[0];
    if (!candidate) {
      return;
    }
    focusNode(candidate.id);
  };

  const handleReset = () => {
    if (fgRef.current && filteredData.nodes.length) {
      setSelectedNodeId(null);
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
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Filter topics by label"
          />
          <button type="button" className="secondary-button" onClick={handleReset}>
            Reset View
          </button>
        </div>
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
                return isConnected ? "rgba(37, 99, 235, 0.82)" : "rgba(148, 163, 184, 0.14)";
              }}
              nodeLabel="id"
              nodeColor={(node) => {
                if (!selectedNodeId) {
                  return graphColor(node.group);
                }
                return focusContext.neighborIds.has(node.id) ? graphColor(node.group) : "rgba(203, 213, 225, 0.28)";
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
                const showLabel = isSelected || hoveredNodeId === node.id || (node.degree || 0) >= 2;

                ctx.beginPath();
                ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI, false);
                ctx.globalAlpha = isDimmed ? 0.2 : 1;
                ctx.fillStyle = graphColor(node.group);
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
                  ctx.arc(node.x, node.y, radius + 4, 0, 2 * Math.PI, false);
                  ctx.strokeStyle = "#f97316";
                  ctx.lineWidth = 2.5;
                  ctx.stroke();
                } else if (selectedNodeId && isNeighbor) {
                  ctx.beginPath();
                  ctx.arc(node.x, node.y, radius + 3, 0, 2 * Math.PI, false);
                  ctx.strokeStyle = "rgba(37, 99, 235, 0.42)";
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
