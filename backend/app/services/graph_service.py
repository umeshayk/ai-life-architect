from collections import Counter, defaultdict
from itertools import combinations

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

from app.models.content_topic import ContentTopic
from app.models.knowledge import KnowledgeItem
from app.schemas.graph import GraphEdge, GraphNode, GraphResponse
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

    for item in items:
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

    nodes = [
        GraphNode(
            id=topic_name,
            label=topic_name,
            type="topic",
            group=_topic_group(topic_name),
            size=10 + min(18, topic_counts[topic_name] * 2.2),
            linked_titles=topic_to_titles[topic_name][:12],
            linked_count=topic_counts[topic_name],
        )
        for topic_name in top_topic_names
    ]

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

    existing_node_ids = {node.id for node in nodes}
    for node in hierarchy_nodes:
        if node.id not in existing_node_ids:
            nodes.append(node)
            existing_node_ids.add(node.id)
    edges.extend(hierarchy_edges)

    return GraphResponse(nodes=nodes, edges=edges)
