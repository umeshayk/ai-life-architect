from collections import Counter, defaultdict
from itertools import combinations

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

from app.models.content_topic import ContentTopic
from app.models.knowledge import KnowledgeItem
from app.schemas.graph import GraphEdge, GraphNode, GraphResponse
from app.services.topic_bridge_service import build_topic_bridges
from app.services.topic_hierarchy_service import build_hierarchy_graph


TOPIC_CATEGORY_MAP = {
    "Embeddings": "AI",
    "Semantic Search": "AI",
    "Vector Databases": "AI",
    "Hybrid Search": "AI",
    "Retrieval Augmented Generation": "AI",
    "Retrieval Optimization": "AI",
    "LLM Systems": "AI",
    "Mushroom Farming": "Agriculture",
    "Hydroponic Farming": "Agriculture",
    "Spawn Quality": "Agriculture",
    "Substrate Sterilization": "Agriculture",
    "Yield Optimization": "Agriculture",
    "Climate Control": "Agriculture",
    "Vedic Mathematics": "Mathematics",
    "Mathematics": "Mathematics",
    "Knowledge Management": "Knowledge",
    "AI Life Architect": "Knowledge",
    "Travel / Spiritual": "Spiritual",
}


def _topic_group(topic_name: str) -> str:
    if topic_name.startswith("AI in ") or " and " in topic_name:
        return "Bridge"
    if topic_name == "Real Estate" or topic_name.endswith(" Property"):
        return "Business"
    return TOPIC_CATEGORY_MAP.get(topic_name, "General")


def build_graph_for_user(db: Session, user_id: int) -> GraphResponse:
    items = db.scalars(
        select(KnowledgeItem)
        .options(selectinload(KnowledgeItem.content_topics).selectinload(ContentTopic.topic))
        .where(KnowledgeItem.user_id == user_id)
        .order_by(desc(KnowledgeItem.updated_at))
        .limit(80)
    ).all()
    if not items:
        return GraphResponse(nodes=[], edges=[])

    topic_counts: Counter[str] = Counter()
    pair_counts: Counter[tuple[str, str]] = Counter()
    topic_to_titles: dict[str, list[str]] = defaultdict(list)
    recent_topic_names: list[str] = []
    recency_weights: Counter[str] = Counter()

    total_items = max(len(items), 1)
    for index, item in enumerate(items):
        topic_names = sorted(
            {
                content_topic.topic.name
                for content_topic in item.content_topics
                if content_topic.topic is not None
            }
        )
        if not topic_names:
            continue

        for topic_name in topic_names:
            topic_counts[topic_name] += 1
            topic_to_titles[topic_name].append(item.title)
            if topic_name not in recent_topic_names:
                recent_topic_names.append(topic_name)
            recency_weights[topic_name] += round(max(0.2, 1.4 - (index / total_items) * 1.1), 2)

        for left, right in combinations(topic_names, 2):
            pair_counts[(left, right)] += 1

    top_topic_names = [topic_name for topic_name, _ in topic_counts.most_common(24)]
    for topic_name in recent_topic_names:
        if topic_name in top_topic_names:
            continue
        top_topic_names.append(topic_name)
        if len(top_topic_names) >= 32:
            break
    top_topic_set = set(top_topic_names)
    if not top_topic_names:
        return GraphResponse(nodes=[], edges=[])

    edges = [
        GraphEdge(
            source=source,
            target=target,
            type="topic_link",
            weight=float(weight),
        )
        for (source, target), weight in pair_counts.most_common(60)
        if source in top_topic_set and target in top_topic_set
    ]

    hierarchy_nodes, hierarchy_edges = build_hierarchy_graph(
        Counter({topic_name: topic_counts[topic_name] for topic_name in top_topic_names}),
        {topic_name: topic_to_titles[topic_name] for topic_name in top_topic_names},
        _topic_group,
    )
    bridge_nodes, bridge_edges = build_topic_bridges(
        db,
        user_id,
        top_topic_names,
        {topic_name: topic_to_titles[topic_name] for topic_name in top_topic_names},
        _topic_group,
    )

    connection_counts: Counter[str] = Counter()
    for edge in edges + hierarchy_edges + bridge_edges:
        connection_counts[edge.source] += 1
        connection_counts[edge.target] += 1

    nodes = [
        GraphNode(
            id=topic_name,
            label=topic_name,
            type="topic",
            group=_topic_group(topic_name),
            size=0,
            importance=round(topic_counts[topic_name] * 2 + connection_counts[topic_name] + recency_weights[topic_name], 2),
            connection_count=connection_counts[topic_name],
            linked_titles=topic_to_titles[topic_name][:12],
            linked_count=topic_counts[topic_name],
        )
        for topic_name in top_topic_names
    ]

    existing_node_ids = {node.id for node in nodes}
    for node in hierarchy_nodes:
        if node.id not in existing_node_ids:
            hierarchy_importance = round(
                node.linked_count * 2 + connection_counts[node.id] + max(0.5, node.linked_count * 0.2),
                2,
            )
            node.importance = hierarchy_importance
            node.connection_count = connection_counts[node.id]
            node.size = 0
            nodes.append(node)
            existing_node_ids.add(node.id)
    for node in bridge_nodes:
        if node.id not in existing_node_ids:
            node.importance = round(node.importance + connection_counts[node.id], 2)
            node.connection_count = connection_counts[node.id]
            node.size = 0
            nodes.append(node)
            existing_node_ids.add(node.id)
    edges.extend(hierarchy_edges)
    edges.extend(bridge_edges)

    for node in nodes:
        node.size = 4 + min(28, node.importance * 2)

    return GraphResponse(nodes=nodes, edges=edges)
