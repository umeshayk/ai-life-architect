import { useEffect, useMemo, useRef, useState } from "react";
import ForceGraph2D from "react-force-graph-2d";
import { useNavigate } from "react-router-dom";
import api from "../api/client";
import LearningPathsPanel from "../components/LearningPathsPanel";

const GROUP_COLORS = {
  AI: "#3b82f6",
  Agriculture: "#22c55e",
  Bridge: "#14b8a6",
  Math: "#a855f7",
  Mathematics: "#a855f7",
  Business: "#f97316",
  Knowledge: "#f97316",
  Spiritual: "#0891b2",
  General: "#9ca3af"
};

const DOMAIN_ICON_STYLES = {
  AI: { background: "#dbeafe", color: "#1d4ed8" },
  Agriculture: { background: "#dcfce7", color: "#15803d" },
  Bridge: { background: "#ccfbf1", color: "#0f766e" },
  Math: { background: "#f3e8ff", color: "#7e22ce" },
  Mathematics: { background: "#f3e8ff", color: "#7e22ce" },
  Business: { background: "#ffedd5", color: "#c2410c" },
  Knowledge: { background: "#ffedd5", color: "#ea580c" },
  Spiritual: { background: "#cffafe", color: "#0e7490" },
  General: { background: "#e2e8f0", color: "#475569" }
};

const DOMAIN_ANCHORS = {
  AI: { x: 0.22, y: 0.42 },
  Agriculture: { x: 0.52, y: 0.22 },
  Bridge: { x: 0.56, y: 0.52 },
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

function createClusterForce(axis, anchorMap, width, height, groupAccessor) {
  let nodes = [];

  const force = (alpha) => {
    const strength = 0.3 * alpha;
    nodes.forEach((node) => {
      const group = groupAccessor(node);
      const anchor = anchorMap.get(group) || { x: width / 2, y: height / 2 };
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

function polarPoint(centerX, centerY, radius, angle) {
  return {
    x: centerX + radius * Math.cos(angle),
    y: centerY + radius * Math.sin(angle)
  };
}

function applyLevelLayout(nodes, width, height, level, activeTopic) {
  const cloned = nodes.map((node) => ({ ...node }));
  const centerX = width / 2;
  const centerY = height / 2;

  if (level === 2) {
    const sorted = [...cloned].sort((a, b) => (b.importance || 0) - (a.importance || 0));
    const innerCount = Math.min(6, sorted.length);
    const innerRadius = Math.min(width, height) * 0.18;
    const outerRadius = Math.min(width, height) * 0.31;
    sorted.forEach((node, index) => {
      const isInner = index < innerCount;
      const ringIndex = isInner ? index : index - innerCount;
      const ringSize = isInner ? innerCount : Math.max(1, sorted.length - innerCount);
      const angle = (-Math.PI / 2) + ((2 * Math.PI * ringIndex) / ringSize);
      const point = polarPoint(centerX, centerY, isInner ? innerRadius : outerRadius, angle);
      node.x = point.x;
      node.y = point.y;
      node.fx = point.x;
      node.fy = point.y;
    });
    return cloned;
  }

  if (level === 3) {
    const focusNode = cloned.find((node) => node.label === activeTopic) || cloned[0];
    const bridgeNodes = cloned.filter((node) => node.type === "bridge");
    const topicNodes = cloned.filter((node) => node.id !== focusNode?.id && node.type !== "bridge");
    if (focusNode) {
      focusNode.x = centerX;
      focusNode.y = centerY;
      focusNode.fx = centerX;
      focusNode.fy = centerY;
    }
    bridgeNodes.forEach((node, index) => {
      const angle = (-Math.PI / 2) + ((2 * Math.PI * index) / Math.max(1, bridgeNodes.length));
      const point = polarPoint(centerX, centerY, Math.min(width, height) * 0.18, angle);
      node.x = point.x;
      node.y = point.y;
      node.fx = point.x;
      node.fy = point.y;
    });
    topicNodes.forEach((node, index) => {
      const angle = (-Math.PI / 2) + ((2 * Math.PI * index) / Math.max(1, topicNodes.length));
      const point = polarPoint(centerX, centerY, Math.min(width, height) * 0.32, angle);
      node.x = point.x;
      node.y = point.y;
      node.fx = point.x;
      node.fy = point.y;
    });
    return cloned;
  }

  if (level >= 4) {
    const rootNode = cloned.find((node) => node.label === activeTopic || node.type === "topic" || node.type === "bridge") || cloned[0];
    const knowledgeNodes = cloned.filter((node) => node.id !== rootNode?.id);
    if (rootNode) {
      rootNode.x = centerX;
      rootNode.y = centerY - 20;
      rootNode.fx = rootNode.x;
      rootNode.fy = rootNode.y;
    }
    knowledgeNodes.forEach((node, index) => {
      const angle = (-Math.PI / 2) + ((2 * Math.PI * index) / Math.max(1, knowledgeNodes.length));
      const point = polarPoint(centerX, centerY + 10, Math.min(width, height) * 0.28, angle);
      node.x = point.x;
      node.y = point.y;
      node.fx = point.x;
      node.fy = point.y;
    });
    return cloned;
  }

  return cloned;
}

function nodeRadius(node, level = 1, activeTopic = "") {
  if (node.type === "knowledge") {
    return level >= 4 ? 6 : 7;
  }
  if (level >= 4) {
    return node.label === activeTopic ? 14 : 6;
  }
  if (level === 3) {
    if (node.type === "bridge") {
      return 8;
    }
    if (node.label === activeTopic) {
      return 13;
    }
  }
  if (typeof node.size === "number" && node.size > 0) {
    return Math.max(4, Math.min(level >= 3 ? 18 : 22, node.size));
  }
  const importance = node.importance || 0;
  if (importance < 1) {
    return 2;
  }
  return Math.min(level >= 3 ? 16 : 20, 4 + importance * (level >= 3 ? 0.9 : 1.2));
}

function levelSummary(level, domain, topic) {
  if (level === 1) {
    return "Level 1: domain clusters";
  }
  if (level === 2) {
    return `Level 2: topics in ${domain || "this domain"}`;
  }
  if (level === 3) {
    return `Level 3: related topics around ${topic || "this topic"}`;
  }
  return `Level 4: saved knowledge items for ${topic || "this topic"}`;
}


function DomainTopicIcon({ domain }) {
  const style = DOMAIN_ICON_STYLES[domain] || DOMAIN_ICON_STYLES.General;

  if (domain === "AI") {
    return (
      <span className="domain-topic-icon" style={style} aria-hidden="true">
        <svg viewBox="0 0 16 16" className="domain-topic-svg">
          <rect x="3" y="4" width="10" height="8" rx="2" fill="none" stroke="currentColor" strokeWidth="1.6" />
          <path d="M6 2.5v2M10 2.5v2M5 7h.01M11 7h.01M6 10h4" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
        </svg>
      </span>
    );
  }

  if (domain === "Agriculture") {
    return (
      <span className="domain-topic-icon" style={style} aria-hidden="true">
        <svg viewBox="0 0 16 16" className="domain-topic-svg">
          <path d="M8 13V8" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
          <path d="M8 8c0-2.6 2-4.2 4.5-4.5-.3 2.5-1.9 4.5-4.5 4.5Z" fill="currentColor" opacity="0.9" />
          <path d="M8 9c0-2.1-1.6-3.4-3.8-3.7.2 2.1 1.6 3.7 3.8 3.7Z" fill="currentColor" opacity="0.65" />
          <path d="M5.5 13h5" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
        </svg>
      </span>
    );
  }

  if (domain === "Knowledge") {
    return (
      <span className="domain-topic-icon" style={style} aria-hidden="true">
        <svg viewBox="0 0 16 16" className="domain-topic-svg">
          <path d="M4 3.5h6.5A1.5 1.5 0 0 1 12 5v7H5.5A1.5 1.5 0 0 0 4 13.5v-10Z" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
          <path d="M4 12.5A1.5 1.5 0 0 1 5.5 11H12" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      </span>
    );
  }

  if (domain === "Business") {
    return (
      <span className="domain-topic-icon" style={style} aria-hidden="true">
        <svg viewBox="0 0 16 16" className="domain-topic-svg">
          <rect x="3" y="5" width="10" height="7.5" rx="1.5" fill="none" stroke="currentColor" strokeWidth="1.5" />
          <path d="M6 5V4a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v1M3 8h10" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      </span>
    );
  }

  if (domain === "Math" || domain === "Mathematics") {
    return (
      <span className="domain-topic-icon" style={style} aria-hidden="true">
        <svg viewBox="0 0 16 16" className="domain-topic-svg">
          <rect x="4" y="2.5" width="8" height="11" rx="1.5" fill="none" stroke="currentColor" strokeWidth="1.5" />
          <path d="M6 5.5h4M6 8h4M6 10.5h4" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      </span>
    );
  }

  if (domain === "Spiritual") {
    return (
      <span className="domain-topic-icon" style={style} aria-hidden="true">
        <svg viewBox="0 0 16 16" className="domain-topic-svg">
          <path d="M8 2.5c1.8 2 2.7 3.3 2.7 4.7A2.7 2.7 0 1 1 5.3 7.2C5.3 5.8 6.2 4.5 8 2.5Z" fill="currentColor" opacity="0.85" />
          <path d="M8 9.5v3M6 12.5h4" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      </span>
    );
  }

  if (domain === "Bridge") {
    return (
      <span className="domain-topic-icon" style={style} aria-hidden="true">
        <svg viewBox="0 0 16 16" className="domain-topic-svg">
          <path d="M3 11h10M4 11V8.5a4 4 0 0 1 8 0V11" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M6 11V9.5M8 11V9.5M10 11V9.5" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      </span>
    );
  }

  return (
    <span className="domain-topic-icon" style={style} aria-hidden="true">
      <svg viewBox="0 0 16 16" className="domain-topic-svg">
        <circle cx="8" cy="8" r="3.5" fill="currentColor" opacity="0.2" />
        <path d="M8 3.5v9M3.5 8h9" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
    </span>
  );
}

export default function BrainMap() {
  const navigate = useNavigate();
  const fgRef = useRef(null);
  const shellRef = useRef(null);
  const didAutoFitRef = useRef(false);
  const lastSearchFocusRef = useRef("");
  const [graph, setGraph] = useState({ nodes: [], edges: [], level: 1, domain: null, topic: null, available_domains: [] });
  const [currentLevel, setCurrentLevel] = useState(1);
  const [currentDomain, setCurrentDomain] = useState("");
  const [currentTopic, setCurrentTopic] = useState("");
  const [historyStack, setHistoryStack] = useState([]);
  const [selectedNodeId, setSelectedNodeId] = useState(null);
  const [hoveredNodeId, setHoveredNodeId] = useState(null);
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  const [learningPaths, setLearningPaths] = useState([]);
  const [learningPathsError, setLearningPathsError] = useState("");
  const [graphSize, setGraphSize] = useState({ width: 1200, height: 920 });

  useEffect(() => {
    api
      .get("/api/learning-paths")
      .then((response) => {
        setLearningPaths(response.data || []);
        setLearningPathsError("");
      })
      .catch((err) => setLearningPathsError(err.response?.data?.detail || "Unable to load learning paths."));
  }, []);

  useEffect(() => {
    const params = { level: currentLevel };
    if (currentDomain) {
      params.domain = currentDomain;
    }
    if (currentTopic) {
      params.topic = currentTopic;
    }

    setError("");
    setSelectedNodeId(null);
    api
      .get("/api/brain-map", { params })
      .then((response) => {
        setGraph(response.data);
        didAutoFitRef.current = false;
      })
      .catch((err) => setError(err.response?.data?.detail || "Unable to load the brain map."));
  }, [currentLevel, currentDomain, currentTopic]);

  useEffect(() => {
    const updateSize = () => {
      const nextWidth = Math.max(720, shellRef.current?.clientWidth || 1200);
      setGraphSize({ width: nextWidth, height: 920 });
    };

    updateSize();
    window.addEventListener("resize", updateSize);
    return () => window.removeEventListener("resize", updateSize);
  }, []);

  useEffect(() => {
    if (selectedNodeId || !graph.nodes.length) {
      return;
    }

    const preferredLabel = currentTopic || graph.topic || "";
    if (preferredLabel) {
      const matchingNode = graph.nodes.find((node) => node.label === preferredLabel);
      if (matchingNode) {
        setSelectedNodeId(matchingNode.id);
        return;
      }
    }

    if ((graph.level || currentLevel) === 1) {
      return;
    }

    if (currentDomain || graph.domain) {
      const domainGroup = currentDomain || graph.domain;
      const leadNode = [...graph.nodes]
        .filter((node) => node.group === domainGroup || node.label === domainGroup)
        .sort((left, right) => (right.importance || 0) - (left.importance || 0))[0];
      if (leadNode) {
        setSelectedNodeId(leadNode.id);
      }
    }
  }, [currentDomain, currentLevel, currentTopic, graph, selectedNodeId]);


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
      nodes: applyLevelLayout(graphWithDegree.nodes, graphSize.width, graphSize.height, currentLevel, currentTopic),
      links: graphWithDegree.edges.map((edge) => ({ ...edge }))
    }),
    [currentLevel, currentTopic, graphSize, graphWithDegree]
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
  const selectedGroup = selectedNode?.group || graph.domain || null;
  const availableGroups = useMemo(() => {
    const groups = new Set(filteredData.nodes.map((node) => node.group));
    return Object.entries(GROUP_COLORS).map(([group, color]) => ({
      group,
      color,
      hasNodes: groups.has(group)
    }));
  }, [filteredData.nodes]);
  const clusterAnchors = useMemo(
    () => createClusterAnchors(new Set(filteredData.nodes.map((node) => node.type === "domain" ? node.label : node.group)), graphSize.width, graphSize.height),
    [filteredData.nodes, graphSize]
  );
  const groupLeaders = useMemo(() => {
    const leaders = new Map();
    filteredData.nodes.forEach((node) => {
      const leaderKey = node.type === "domain" ? node.label : node.group;
      const existing = leaders.get(leaderKey);
      if (!existing || (node.importance || 0) > (existing.importance || 0)) {
        leaders.set(leaderKey, node);
      }
    });
    return leaders;
  }, [filteredData.nodes]);

  const focusContext = useMemo(() => {
    if (!selectedNodeId) {
      return { neighborIds: new Set(), connectedLabels: [] };
    }

    const neighborIds = new Set([selectedNodeId]);
    const connectedLabelSet = new Set();

    filteredData.links.forEach((edge) => {
      const sourceId = typeof edge.source === "object" ? edge.source.id : edge.source;
      const targetId = typeof edge.target === "object" ? edge.target.id : edge.target;
      if (sourceId === selectedNodeId) {
        neighborIds.add(targetId);
        connectedLabelSet.add(targetId);
      } else if (targetId === selectedNodeId) {
        neighborIds.add(sourceId);
        connectedLabelSet.add(sourceId);
      }
    });

    return { neighborIds, connectedLabels: Array.from(connectedLabelSet) };
  }, [filteredData, selectedNodeId]);

  const clusterLabels = useMemo(
    () => filteredData.nodes
      .filter((node) => node.type === "domain")
      .map((node) => {
        const anchor = clusterAnchors.get(node.label) || { x: graphSize.width / 2, y: graphSize.height / 2 };
        return {
          group: node.label,
          color: GROUP_COLORS[node.label] || GROUP_COLORS.General,
          label: String(node.label || "General").toUpperCase(),
          x: anchor.x,
          y: Math.max(36, anchor.y - 74)
        };
      }),
    [clusterAnchors, filteredData.nodes, graphSize]
  );

  useEffect(() => {
    if (!fgRef.current || !filteredData.nodes.length) {
      return;
    }

    const graphApi = fgRef.current;
    const groupAccessor = (node) => (node.type === "domain" ? node.label : node.group);
    didAutoFitRef.current = false;
    graphApi.d3Force("charge").strength(currentLevel >= 2 ? 0 : -900);
    graphApi.d3Force("link").distance((link) => {
      if (currentLevel >= 4) {
        return 150;
      }
      if (currentLevel === 3) {
        return 170 + (link.weight || 1) * 12;
      }
      return Math.max(160, graphSize.width / 6) + (link.weight || 1) * 18;
    });
    graphApi.d3Force("center").strength(currentLevel >= 2 ? 0.05 : 0.3);
    graphApi.d3Force("cluster-x", currentLevel === 1 ? createClusterForce("x", clusterAnchors, graphSize.width, graphSize.height, groupAccessor) : null);
    graphApi.d3Force("cluster-y", currentLevel === 1 ? createClusterForce("y", clusterAnchors, graphSize.width, graphSize.height, groupAccessor) : null);
    graphApi.d3Force("leader-x", currentLevel === 1 ? createLeaderForce("x", groupLeaders) : null);
    graphApi.d3Force("leader-y", currentLevel === 1 ? createLeaderForce("y", groupLeaders) : null);
    graphApi.d3Force("collision", null);
    graphApi.d3ReheatSimulation();
  }, [clusterAnchors, currentLevel, filteredData, graphSize, groupLeaders]);

  const focusNode = (nodeId) => {
    setSelectedNodeId(nodeId);
    const targetNode = filteredData.nodes.find((node) => node.id === nodeId);
    if (targetNode && fgRef.current) {
      fgRef.current.centerAt(targetNode.x, targetNode.y, 500);
      fgRef.current.zoom(currentLevel >= 4 ? 2.5 : 2.1, 500);
    }
  };

  const openContext = ({ level, domain = "", topic = "" }) => {
    setHistoryStack((prev) => [...prev, { level: currentLevel, domain: currentDomain, topic: currentTopic }]);
    setCurrentLevel(level);
    setCurrentDomain(domain);
    setCurrentTopic(topic);
    setSelectedNodeId(null);
    lastSearchFocusRef.current = "";
  };

  const drillIntoNode = (node) => {
    if (!node) {
      return;
    }

    if (currentLevel === 1 && node.type === "domain") {
      openContext({ level: 2, domain: node.label });
      return;
    }

    if (currentLevel === 2 && node.type === "topic") {
      openContext({ level: 3, domain: currentDomain || node.group, topic: node.label });
      return;
    }

    if (currentLevel === 3 && (node.type === "topic" || node.type === "bridge")) {
      openContext({ level: 4, domain: currentDomain || node.group, topic: node.label });
      return;
    }

    focusNode(node.id);
  };

  const handleNodeAction = (node) => {
    if (!node) {
      return;
    }

    if (selectedNodeId === node.id) {
      drillIntoNode(node);
      return;
    }

    focusNode(node.id);
  };

  const handleSearchSubmit = (event) => {
    event.preventDefault();
    if (!searchMatches.length) {
      return;
    }
    handleNodeAction(searchMatches[0]);
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
    if (currentLevel === 1) {
      openContext({ level: 2, domain: group });
      return;
    }
    if (group !== "Bridge" && group !== (currentDomain || group) && graph.available_domains?.includes(group)) {
      openContext({ level: 2, domain: group });
      return;
    }
    const candidate = [...filteredData.nodes]
      .filter((node) => node.group === group || node.label === group)
      .sort((left, right) => (right.importance || 0) - (left.importance || 0))[0];
    if (candidate) {
      focusNode(candidate.id);
    }
  };

  const handleBack = () => {
    const previous = historyStack[historyStack.length - 1];
    if (!previous) {
      return;
    }
    setHistoryStack((prev) => prev.slice(0, -1));
    setCurrentLevel(previous.level);
    setCurrentDomain(previous.domain);
    setCurrentTopic(previous.topic);
    setSelectedNodeId(null);
    lastSearchFocusRef.current = "";
  };

  const handleReset = () => {
    setHistoryStack([]);
    setCurrentLevel(1);
    setCurrentDomain("");
    setCurrentTopic("");
    setSelectedNodeId(null);
    setSearch("");
    lastSearchFocusRef.current = "";
    if (fgRef.current && filteredData.nodes.length) {
      fgRef.current.zoomToFit(600, 40);
    }
  };

  const openRelatedTopic = (label) => {
    if (!label) {
      return;
    }
    openContext({ level: 3, domain: currentDomain || selectedNode?.group || "", topic: label });
  };

  const getSuggestionLabel = (suggestion) => suggestion.topic || suggestion.suggested_topic;

  const handleSuggestedTopicClick = (suggestion) => {
    const suggestionLabel = getSuggestionLabel(suggestion);
    const existingNode = graphWithDegree.nodes.find((node) => node.label.toLowerCase() === suggestionLabel.toLowerCase());
    if (existingNode) {
      if (existingNode.type === "domain") {
        openContext({ level: 2, domain: existingNode.label });
        return;
      }
      openContext({ level: 3, domain: suggestion.domain || existingNode.group || currentDomain, topic: existingNode.label });
      return;
    }
    navigate(`/knowledge?topic=${encodeURIComponent(suggestionLabel)}`);
  };

  const handleSuggestionAction = (suggestion) => {
    if (suggestion.action === "focus") {
      handleSuggestedTopicClick(suggestion);
      return;
    }
    navigate(`/knowledge?topic=${encodeURIComponent(getSuggestionLabel(suggestion))}`);
  };

  return (
    <div className="stack">
      <section className="card">
        <h2>Brain Map</h2>
        <p className="muted">Explore how your saved knowledge expands from domains into topics, relationships, bridges, and notes.</p>
      </section>

      <section className="brain-map-layout">
        <div className="card brain-map-main-card">
          <div className="brain-map-toolbar">
          <form className="brain-map-search" onSubmit={handleSearchSubmit}>
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder={currentLevel >= 4 ? "Search items in this view" : "Search and focus this view"}
            />
          </form>
          <button type="button" className="secondary-button" onClick={handleBack} disabled={!historyStack.length}>
            Back
          </button>
          <button type="button" className="secondary-button" onClick={handleReset}>
            Reset View
          </button>
        </div>
        <p className="muted">{levelSummary(graph.level || currentLevel, graph.domain || currentDomain, graph.topic || currentTopic)}</p>
        {!!searchMatches.length && (
          <div className="brain-map-search-results">
            {searchMatches.map((match) => (
              <button
                key={match.id}
                type="button"
                className="brain-map-search-result"
                onClick={() => handleNodeAction(match)}
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
            {graph.level === 1 && (
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
                    onClick={() => openContext({ level: 2, domain: cluster.group })}
                    title={`Open ${cluster.group}`}
                  >
                    <span className="brain-map-cluster-dot" style={{ backgroundColor: cluster.color }} />
                    {cluster.label}
                  </button>
                ))}
              </div>
            )}
            <ForceGraph2D
              ref={fgRef}
              width={graphSize.width}
              height={graphSize.height}
              graphData={filteredData}
              nodeRelSize={6}
              nodeVal={(node) => nodeRadius(node, currentLevel, currentTopic)}
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
              onNodeClick={handleNodeAction}
              nodeCanvasObject={(node, ctx, globalScale) => {
                const label = node.label;
                const fontSize = Math.max(11, 15 / globalScale);
                const radius = nodeRadius(node, currentLevel, currentTopic);
                const isSelected = selectedNodeId === node.id;
                const isNeighbor = focusContext.neighborIds.has(node.id);
                const isDimmed = selectedNodeId && !isNeighbor;
                const isPrimaryLevelThreeNode = currentLevel === 3 && (node.label === currentTopic || node.type === "bridge");
                const isPrimaryLevelFourNode = currentLevel === 4 && node.label === currentTopic;
                const showLabel = isSelected
                  || hoveredNodeId === node.id
                  || node.type === "domain"
                  || isPrimaryLevelThreeNode
                  || isPrimaryLevelFourNode
                  || currentLevel === 2
                  || (currentLevel === 4 && node.type === "knowledge" && filteredData.nodes.length <= 10)
                  || (currentLevel < 2 && (node.importance || 0) >= 5 && radius <= 16);

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
        </div>

        <aside className="brain-map-side-column">
          <LearningPathsPanel
            learningPaths={learningPaths}
            error={learningPathsError}
            onTopicClick={handleSuggestedTopicClick}
            onTopicAction={handleSuggestionAction}
          />

          <section className="card brain-side-card">
            <h3>Details</h3>
        {!selectedNode ? (
          <p className="muted">Click a node to inspect its related knowledge or zoom deeper into the map.</p>
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
                <p className="source-meta">Directly connected nodes</p>
                <div className="tag-list">
                  {focusContext.connectedLabels.map((label) => (
                    <button
                      key={`${selectedNode.id}-${label}`}
                      type="button"
                      className="tag tag-button"
                      onClick={() => currentLevel >= 3 ? openRelatedTopic(label) : focusNode(label)}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {selectedNode.summary && <p className="muted">{selectedNode.summary}</p>}
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
              Suggested next step: {currentLevel < 4 && (selectedNode.type === "domain" || selectedNode.type === "topic" || selectedNode.type === "bridge")
                ? "Click the selected node again or use Zoom Deeper."
                : focusContext.connectedLabels[0]
                  ? `Explore ${focusContext.connectedLabels[0]}`
                  : "Open this item to review it in full."}
            </p>
            <div className="brain-detail-actions">
              {currentLevel < 4 && (selectedNode.type === "domain" || selectedNode.type === "topic" || selectedNode.type === "bridge") && (
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => drillIntoNode(selectedNode)}
                >
                  Zoom Deeper
                </button>
              )}
              {(selectedNode.type === "topic" || selectedNode.type === "bridge") && (
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => navigate(`/topics/${encodeURIComponent(selectedNode.label)}`)}
                >
                  Open Topic Page
                </button>
              )}
              {selectedNode.type === "knowledge" && (
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => navigate(`/knowledge?focus=${encodeURIComponent(selectedNode.id.replace("knowledge-", ""))}`)}
                >
                  Open Note
                </button>
              )}
            </div>
          </div>
        )}
          </section>
        </aside>
      </section>
    </div>
  );
}


