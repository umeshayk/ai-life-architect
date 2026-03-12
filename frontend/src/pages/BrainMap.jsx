import { useEffect, useMemo, useRef, useState } from "react";
import ForceGraph2D from "react-force-graph-2d";
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

export default function BrainMap() {
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

  const handleReset = () => {
    if (fgRef.current && filteredData.nodes.length) {
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
              nodeVal={(node) => Math.min(32, 5 + (node.degree || 1) * 3)}
              cooldownTicks={160}
              onEngineStop={() => {
                if (!didAutoFitRef.current && fgRef.current) {
                  fgRef.current.zoomToFit(700, 40);
                  didAutoFitRef.current = true;
                }
              }}
              linkWidth={1.5}
              linkColor={() => "rgba(59, 130, 246, 0.38)"}
              nodeLabel="id"
              nodeColor={(node) => graphColor(node.group)}
              enableNodeDrag={true}
              onNodeHover={(node) => setHoveredNodeId(node?.id || null)}
              onNodeClick={(node) => {
                setSelectedNodeId(node.id);
                fgRef.current?.centerAt(node.x, node.y, 500);
              }}
              nodeCanvasObject={(node, ctx, globalScale) => {
                const label = node.label;
                const fontSize = Math.max(11, 15 / globalScale);
                const radius = Math.min(32, 5 + (node.degree || 1) * 3);

                ctx.beginPath();
                ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI, false);
                ctx.fillStyle = graphColor(node.group);
                ctx.fill();

                if (selectedNodeId === node.id || hoveredNodeId === node.id) {
                  ctx.font = `${fontSize}px Segoe UI`;
                  ctx.fillStyle = "#0f172a";
                  ctx.textAlign = "center";
                  ctx.fillText(label, node.x, node.y + radius + fontSize + 2);
                }

                if (selectedNodeId === node.id) {
                  ctx.beginPath();
                  ctx.arc(node.x, node.y, radius + 4, 0, 2 * Math.PI, false);
                  ctx.strokeStyle = "#f97316";
                  ctx.lineWidth = 2.5;
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
            </div>
            <p className="muted">{selectedNode.linked_count} linked item(s)</p>
            {selectedNode.linked_titles?.length > 0 ? (
              <ul className="simple-list">
                {selectedNode.linked_titles.map((title) => (
                  <li key={`${selectedNode.id}-${title}`}>{title}</li>
                ))}
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
