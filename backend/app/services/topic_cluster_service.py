from collections import defaultdict

from app.schemas.graph import GraphNode, GraphResponse


CLUSTER_RULES = {
    "AI": [
        ("Retrieval", ("search", "retrieval", "rag", "keyword", "semantic", "hybrid")),
        ("Representation", ("embedding", "representation", "latent")),
        ("Storage", ("vector database", "vector", "database", "index", "storage")),
        ("Ranking", ("rank", "ranking", "relevance", "optimization")),
    ],
    "Agriculture": [
        ("Agriculture Automation", ("farm", "agriculture", "yield", "hydroponic", "climate", "automation", "mushroom", "substrate", "spawn")),
    ],
    "Knowledge": [
        ("Knowledge Systems", ("knowledge", "planning", "personal knowledge", "action", "architect")),
    ],
    "Business": [
        ("Real Estate", ("property", "real estate", "land", "site", "muda", "mysuru", "commercial")),
    ],
    "General": [
        ("Knowledge Systems", ("knowledge", "planning")),
        ("Real Estate", ("property", "real estate", "land")),
    ],
}


def infer_topic_cluster(topic_name: str, domain: str | None) -> str:
    normalized = (topic_name or "").strip().lower()
    cluster_rules = CLUSTER_RULES.get(domain or "", []) + CLUSTER_RULES.get("General", [])
    for label, keywords in cluster_rules:
        if any(keyword in normalized for keyword in keywords):
            return label
    return domain or "General"


def annotate_graph_clusters(response: GraphResponse, center_topic: str | None = None) -> GraphResponse:
    ranked_nodes: dict[str, int] = {}
    bucketed: dict[str, list[GraphNode]] = defaultdict(list)

    for node in response.nodes:
        if node.type not in {"topic", "bridge"}:
            continue
        domain = response.domain or (node.group if node.group and node.group not in {"Bridge", "General"} else None) or node.group or "General"
        cluster = infer_topic_cluster(node.label, domain)
        updated_node = node.model_copy(update={
            "domain": domain,
            "cluster": cluster,
            "centrality": round(float(node.importance or 0.0), 2),
            "is_center": bool(center_topic and node.label == center_topic),
        })
        bucketed[cluster].append(updated_node)

    for cluster_nodes in bucketed.values():
        ordered = sorted(
            cluster_nodes,
            key=lambda item: (
                0 if item.is_center else 1,
                -(item.centrality or 0.0),
                item.label,
            ),
        )
        for index, node in enumerate(ordered, start=1):
            ranked_nodes[node.id] = index

    annotated_nodes: list[GraphNode] = []
    for node in response.nodes:
        domain = node.domain or response.domain or (node.group if node.group and node.group not in {"Bridge", "General"} else None) or node.group or "General"
        cluster = node.cluster or infer_topic_cluster(node.label, domain)
        annotated_nodes.append(
            node.model_copy(update={
                "domain": domain,
                "cluster": cluster,
                "cluster_rank": ranked_nodes.get(node.id),
                "centrality": round(float(node.importance or 0.0), 2),
                "is_center": bool(center_topic and node.label == center_topic),
            })
        )

    return response.model_copy(update={"nodes": annotated_nodes})
