from collections import Counter, defaultdict
from itertools import combinations

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

from app.models.content_topic import ContentTopic
from app.models.knowledge import KnowledgeItem
from app.schemas.graph import GraphEdge, GraphNode, GraphResponse


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

        for left, right in combinations(topic_names, 2):
            pair_counts[(left, right)] += 1

    top_topic_names = [topic_name for topic_name, _ in topic_counts.most_common(24)]
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

    connected_topics = {edge.source for edge in edges} | {edge.target for edge in edges}
    if connected_topics:
        nodes = [node for node in nodes if node.id in connected_topics]

    return GraphResponse(nodes=nodes, edges=edges)
