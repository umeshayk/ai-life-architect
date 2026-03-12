import { useEffect, useMemo, useRef, useState } from "react";
import api from "../api/client";

const WIDTH = 1200;
const HEIGHT = 920;

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function computeFitViewport(nodes) {
  if (!nodes.length) {
    return { scale: 1, x: 0, y: 0 };
  }

  const padding = 90;
  const xs = nodes.map((node) => node.x);
  const ys = nodes.map((node) => node.y);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const graphWidth = Math.max(1, maxX - minX);
  const graphHeight = Math.max(1, maxY - minY);
  const scale = clamp(
    Math.min((WIDTH - padding * 2) / graphWidth, (HEIGHT - padding * 2) / graphHeight),
    0.55,
    1.35
  );

  return {
    scale,
    x: (WIDTH - graphWidth * scale) / 2 - minX * scale,
    y: (HEIGHT - graphHeight * scale) / 2 - minY * scale
  };
}

function buildLayout(nodes) {
  const topicNodes = nodes.filter((node) => node.type === "topic");
  const knowledgeNodes = nodes.filter((node) => node.type === "knowledge");
  const positioned = {};
  const topicSlots = new Map();
  const topicLoad = new Map();

  topicNodes.forEach((node, index) => {
    const columnCount = Math.max(2, Math.ceil(Math.sqrt(topicNodes.length)));
    const row = Math.floor(index / columnCount);
    const column = index % columnCount;
    const rowCount = Math.max(1, Math.ceil(topicNodes.length / columnCount));
    const x = 120 + (column * (WIDTH - 240)) / Math.max(1, columnCount - 1);
    const y = 110 + (row * (HEIGHT - 220)) / Math.max(1, rowCount - 1);

    positioned[node.id] = {
      ...node,
      x,
      y
    };
    topicSlots.set(node.label, { x, y });
    topicLoad.set(node.label, 0);
  });

  knowledgeNodes.forEach((node, index) => {
    const primaryTopic = node.topics?.find((topic) => topicSlots.has(topic));
    const clusterCenter = primaryTopic
      ? topicSlots.get(primaryTopic)
      : {
          x: 120 + (index * (WIDTH - 240)) / Math.max(1, knowledgeNodes.length - 1),
          y: HEIGHT - 120 - (index % 4) * 90
        };
    const clusterIndex = primaryTopic ? topicLoad.get(primaryTopic) || 0 : index;
    const angle = clusterIndex * 1.6;
    const radius = 170 + Math.floor(clusterIndex / 5) * 80;
    const x = clamp(clusterCenter.x + Math.cos(angle) * radius, 50, WIDTH - 50);
    const y = clamp(clusterCenter.y + Math.sin(angle) * (radius * 0.82), 60, HEIGHT - 60);

    positioned[node.id] = {
      ...node,
      x,
      y
    };
    if (primaryTopic) {
      topicLoad.set(primaryTopic, clusterIndex + 1);
    }
  });

  return nodes.map((node) => positioned[node.id] || node);
}

export default function BrainMap() {
  const [graph, setGraph] = useState({ nodes: [], edges: [] });
  const [selectedNodeId, setSelectedNodeId] = useState(null);
  const [search, setSearch] = useState("");
  const [showTopicLinks, setShowTopicLinks] = useState(true);
  const [showSemanticLinks, setShowSemanticLinks] = useState(true);
  const [viewport, setViewport] = useState({ scale: 1, x: 0, y: 0 });
  const [hoveredNodeId, setHoveredNodeId] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState("");
  const dragRef = useRef({ x: 0, y: 0 });
  const fitFrameRef = useRef(null);
  const canvasRef = useRef(null);

  useEffect(() => {
    api
      .get("/api/graph")
      .then((response) => setGraph(response.data))
      .catch((err) => setError(err.response?.data?.detail || "Unable to load the brain map."));
  }, []);

  const filteredNodes = useMemo(() => {
    const labelQuery = search.trim().toLowerCase();
    const sourceNodes = labelQuery
      ? graph.nodes.filter((node) => node.label.toLowerCase().includes(labelQuery))
      : graph.nodes;
    return buildLayout(sourceNodes);
  }, [graph.nodes, search]);

  const filteredNodeIds = useMemo(() => new Set(filteredNodes.map((node) => node.id)), [filteredNodes]);

  const filteredEdges = useMemo(
    () =>
      graph.edges.filter((edge) => {
        if (!filteredNodeIds.has(edge.source) || !filteredNodeIds.has(edge.target)) {
          return false;
        }
        if (edge.type === "topic_link" && !showTopicLinks) {
          return false;
        }
        if (edge.type === "semantic_related" && !showSemanticLinks) {
          return false;
        }
        return true;
      }),
    [graph.edges, filteredNodeIds, showTopicLinks, showSemanticLinks]
  );

  const nodeMap = useMemo(
    () => Object.fromEntries(filteredNodes.map((node) => [node.id, node])),
    [filteredNodes]
  );

  const selectedNode = selectedNodeId ? graph.nodes.find((node) => node.id === selectedNodeId) : null;

  useEffect(() => {
    if (fitFrameRef.current) {
      cancelAnimationFrame(fitFrameRef.current);
    }
    fitFrameRef.current = requestAnimationFrame(() => {
      fitFrameRef.current = requestAnimationFrame(() => {
        setViewport(computeFitViewport(filteredNodes));
      });
    });

    return () => {
      if (fitFrameRef.current) {
        cancelAnimationFrame(fitFrameRef.current);
      }
    };
  }, [filteredNodes, showTopicLinks, showSemanticLinks]);

  useEffect(() => {
    const handleResize = () => {
      if (fitFrameRef.current) {
        cancelAnimationFrame(fitFrameRef.current);
      }
      fitFrameRef.current = requestAnimationFrame(() => {
        setViewport(computeFitViewport(filteredNodes));
      });
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [filteredNodes]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) {
      return undefined;
    }

    const handleWheel = (event) => {
      event.preventDefault();
      setViewport((current) => ({
        ...current,
        scale: clamp(current.scale + (event.deltaY < 0 ? 0.08 : -0.08), 0.5, 1.8)
      }));
    };

    canvas.addEventListener("wheel", handleWheel, { passive: false });
    return () => canvas.removeEventListener("wheel", handleWheel);
  }, [filteredNodes.length]);

  const handleMouseDown = (event) => {
    if (event.target.dataset.node === "true") {
      return;
    }
    setDragging(true);
    dragRef.current = { x: event.clientX, y: event.clientY };
  };

  const handleMouseMove = (event) => {
    if (!dragging) {
      return;
    }
    const dx = event.clientX - dragRef.current.x;
    const dy = event.clientY - dragRef.current.y;
    dragRef.current = { x: event.clientX, y: event.clientY };
    setViewport((current) => ({ ...current, x: current.x + dx, y: current.y + dy }));
  };

  const handleMouseUp = () => {
    setDragging(false);
  };

  const resetView = () => setViewport(computeFitViewport(filteredNodes));

  const focusNode = (nodeId) => {
    setSelectedNodeId(nodeId);
  };

  return (
    <div className="stack">
      <section className="card">
        <h2>Brain Map</h2>
        <p className="muted">Explore how your saved knowledge connects.</p>
      </section>

      <section className="card">
        <div className="brain-map-toolbar">
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Filter nodes by label"
          />
          <label className="toggle-chip">
            <input
              type="checkbox"
              checked={showTopicLinks}
              onChange={(event) => setShowTopicLinks(event.target.checked)}
            />
            Topic Links
          </label>
          <label className="toggle-chip">
            <input
              type="checkbox"
              checked={showSemanticLinks}
              onChange={(event) => setShowSemanticLinks(event.target.checked)}
            />
            Semantic Links
          </label>
          <button type="button" className="secondary-button" onClick={resetView}>
            Reset View
          </button>
        </div>

        {error && <p className="error-text">{error}</p>}
        {!error && filteredNodes.length === 0 ? (
          <p className="muted">No graph data available yet. Add knowledge, topics, and connections first.</p>
        ) : (
          <div
            ref={canvasRef}
            className="brain-map-canvas"
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
          >
            <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="brain-map-svg">
              <g transform={`translate(${viewport.x}, ${viewport.y}) scale(${viewport.scale})`}>
                {filteredEdges.map((edge, index) => {
                  const source = nodeMap[edge.source];
                  const target = nodeMap[edge.target];
                  if (!source || !target) {
                    return null;
                  }
                  return (
                    <line
                      key={`${edge.source}-${edge.target}-${edge.type}-${index}`}
                      x1={source.x}
                      y1={source.y}
                      x2={target.x}
                      y2={target.y}
                      className={`graph-edge ${edge.type}`}
                    />
                  );
                })}

                {filteredNodes.map((node) => (
                  <g
                    key={node.id}
                    transform={`translate(${node.x}, ${node.y})`}
                    className={`graph-node ${node.type} ${selectedNodeId === node.id ? "selected" : ""}`}
                    onClick={() => focusNode(node.id)}
                    onMouseEnter={() => setHoveredNodeId(node.id)}
                    onMouseLeave={() => setHoveredNodeId((current) => (current === node.id ? null : current))}
                    data-node="true"
                  >
                    <title>{node.label}</title>
                    <circle r={node.size} data-node="true" />
                    {(selectedNodeId === node.id ||
                      hoveredNodeId === node.id ||
                      node.type === "topic") && (
                      <text y={node.size + 18} textAnchor="middle" data-node="true">
                        {node.label.length > 24 ? `${node.label.slice(0, 24)}...` : node.label}
                      </text>
                    )}
                  </g>
                ))}
              </g>
            </svg>
          </div>
        )}
      </section>

      <section className="card">
        <h3>Details</h3>
        {!selectedNode ? (
          <p className="muted">Click a topic or knowledge node to inspect it.</p>
        ) : selectedNode.type === "knowledge" ? (
          <div className="stack compact">
            <div className="brain-detail-header">
              <strong>{selectedNode.label}</strong>
              <span className="tag">{selectedNode.content_type || selectedNode.group}</span>
            </div>
            <p>{selectedNode.summary || "No summary available."}</p>
            {selectedNode.tags?.length > 0 && (
              <div className="tag-list">
                {selectedNode.tags.map((tag) => (
                  <span key={`${selectedNode.id}-tag-${tag}`} className="tag">{tag}</span>
                ))}
              </div>
            )}
            {selectedNode.topics?.length > 0 && (
              <div className="tag-list">
                {selectedNode.topics.map((topic) => (
                  <span key={`${selectedNode.id}-topic-${topic}`} className="tag">{topic}</span>
                ))}
              </div>
            )}
            <div>
              <h4>Related Knowledge</h4>
              {selectedNode.related_titles?.length > 0 ? (
                <ul className="simple-list">
                  {selectedNode.related_titles.map((title) => {
                    const match = graph.nodes.find((node) => node.label === title && node.type === "knowledge");
                    return (
                      <li key={`${selectedNode.id}-${title}`}>
                        {match ? (
                          <button type="button" className="link-button" onClick={() => focusNode(match.id)}>
                            {title}
                          </button>
                        ) : (
                          title
                        )}
                      </li>
                    );
                  })}
                </ul>
              ) : (
                <p className="muted">No related knowledge connected.</p>
              )}
            </div>
          </div>
        ) : (
          <div className="stack compact">
            <div className="brain-detail-header">
              <strong>{selectedNode.label}</strong>
              <span className="tag">Topic</span>
            </div>
            <p className="muted">{selectedNode.linked_count} linked item(s)</p>
            {selectedNode.linked_titles?.length > 0 ? (
              <ul className="simple-list">
                {selectedNode.linked_titles.map((title) => {
                  const match = graph.nodes.find((node) => node.label === title && node.type === "knowledge");
                  return (
                    <li key={`${selectedNode.id}-${title}`}>
                      {match ? (
                        <button type="button" className="link-button" onClick={() => focusNode(match.id)}>
                          {title}
                        </button>
                      ) : (
                        title
                      )}
                    </li>
                  );
                })}
              </ul>
            ) : (
              <p className="muted">No linked knowledge items.</p>
            )}
          </div>
        )}
      </section>
    </div>
  );
}
