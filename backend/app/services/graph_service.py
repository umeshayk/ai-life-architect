from collections import Counter, defaultdict

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

from app.models.content_topic import ContentTopic
from app.models.knowledge import KnowledgeItem
from app.models.knowledge_connection import KnowledgeConnection
from app.models.topic import Topic
from app.schemas.graph import GraphEdge, GraphNode, GraphResponse


def build_graph_for_user(db: Session, user_id: int) -> GraphResponse:
    items = db.scalars(
        select(KnowledgeItem)
        .options(
            selectinload(KnowledgeItem.content_topics).selectinload(ContentTopic.topic),
            selectinload(KnowledgeItem.outgoing_connections).selectinload(KnowledgeConnection.target_item),
        )
        .where(KnowledgeItem.user_id == user_id)
        .order_by(desc(KnowledgeItem.updated_at))
        .limit(50)
    ).all()
    if not items:
        return GraphResponse(nodes=[], edges=[])

    item_ids = {item.id for item in items}
    topic_counts: Counter[tuple[int, str]] = Counter()
    topic_to_titles: dict[int, list[str]] = defaultdict(list)

    for item in items:
        for content_topic in item.content_topics:
            if content_topic.topic is None:
                continue
            key = (content_topic.topic.id, content_topic.topic.name)
            topic_counts[key] += 1
            topic_to_titles[content_topic.topic.id].append(item.title)

    top_topics = {topic_id for (topic_id, _), _ in topic_counts.most_common(12)}

    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []

    for (topic_id, topic_name), count in topic_counts.most_common(12):
        nodes.append(
            GraphNode(
                id=f"topic-{topic_id}",
                label=topic_name,
                type="topic",
                group="topic",
                size=16 + count * 2,
                linked_titles=topic_to_titles[topic_id][:12],
                linked_count=count,
            )
        )

    for item in items:
        topic_names = [ct.topic.name for ct in item.content_topics if ct.topic is not None]
        related_titles = [
            connection.target_item.title
            for connection in item.outgoing_connections
            if connection.target_item is not None and connection.target_item.id in item_ids
        ][:6]
        nodes.append(
            GraphNode(
                id=f"knowledge-{item.id}",
                label=item.title,
                type="knowledge",
                group=item.type,
                size=12 + min(8, len(topic_names) + len(related_titles)),
                summary=item.summary,
                content_type=item.type,
                tags=[tag.strip() for tag in (item.tags or "").split(",") if tag.strip()],
                topics=topic_names,
                related_titles=related_titles,
                linked_count=len(related_titles),
            )
        )

        for content_topic in item.content_topics:
            if content_topic.topic is None or content_topic.topic.id not in top_topics:
                continue
            edges.append(
                GraphEdge(
                    source=f"topic-{content_topic.topic.id}",
                    target=f"knowledge-{item.id}",
                    type="topic_link",
                )
            )

    seen_pairs: set[tuple[str, str]] = set()
    for item in items:
        for connection in item.outgoing_connections:
            if connection.target_item is None or connection.target_item.id not in item_ids:
                continue
            source = f"knowledge-{item.id}"
            target = f"knowledge-{connection.target_item.id}"
            pair = tuple(sorted((source, target)))
            if pair in seen_pairs or source == target:
                continue
            seen_pairs.add(pair)
            edges.append(GraphEdge(source=source, target=target, type="semantic_related"))

    return GraphResponse(nodes=nodes, edges=edges)
