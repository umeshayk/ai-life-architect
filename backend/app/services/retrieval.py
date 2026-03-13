from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.content_topic import ContentTopic
from app.models.embedding import KnowledgeEmbedding
from app.models.knowledge import KnowledgeItem
from app.schemas.knowledge import RelatedKnowledgeNote, RelatedKnowledgeResponse
from app.services.embeddings import ensure_user_embeddings, generate_embedding

IGNORED_RELATED_TOPICS = {
    "key concept",
    "why matter",
    "example",
    "notes",
    "definition",
    "topic",
}


@dataclass
class SearchMatch:
    item: KnowledgeItem
    similarity: float


def semantic_search(db: Session, user_id: int, query: str, limit: int = 5) -> list[SearchMatch]:
    ensure_user_embeddings(db, user_id)
    query_vector = generate_embedding(query)
    distance = KnowledgeEmbedding.embedding.cosine_distance(query_vector).label("distance")
    stmt = (
        select(KnowledgeItem, distance)
        .join(KnowledgeEmbedding, KnowledgeEmbedding.knowledge_item_id == KnowledgeItem.id)
        .options(selectinload(KnowledgeItem.content_topics).selectinload(ContentTopic.topic))
        .where(KnowledgeItem.user_id == user_id)
        .order_by(distance)
        .limit(limit)
    )
    rows = db.execute(stmt).all()
    return [
        SearchMatch(item=item, similarity=round(max(0.0, 1.0 - float(distance_value)), 4))
        for item, distance_value in rows
    ]


def find_related_knowledge_by_topics(db: Session, user_id: int, item_id: int, limit: int = 5) -> RelatedKnowledgeResponse | None:
    current_item = db.scalar(
        select(KnowledgeItem)
        .options(selectinload(KnowledgeItem.content_topics).selectinload(ContentTopic.topic))
        .where(KnowledgeItem.id == item_id, KnowledgeItem.user_id == user_id)
    )
    if current_item is None:
        return None

    current_topics = sorted(
        {
            content_topic.topic.name
            for content_topic in current_item.content_topics
            if content_topic.topic is not None and content_topic.topic.name.lower() not in IGNORED_RELATED_TOPICS
        }
    )
    if not current_topics:
        return RelatedKnowledgeResponse(related_topics=[], related_notes=[])

    candidates = db.scalars(
        select(KnowledgeItem)
        .options(selectinload(KnowledgeItem.content_topics).selectinload(ContentTopic.topic))
        .where(KnowledgeItem.user_id == user_id, KnowledgeItem.id != item_id)
    ).all()

    ranked_notes = []
    related_topics = set(current_topics)
    current_topic_set = set(current_topics)

    for candidate in candidates:
        candidate_topics = {
            content_topic.topic.name
            for content_topic in candidate.content_topics
            if content_topic.topic is not None and content_topic.topic.name.lower() not in IGNORED_RELATED_TOPICS
        }
        shared_topics = sorted(current_topic_set.intersection(candidate_topics))
        if not shared_topics:
            continue
        related_topics.update(candidate_topics)
        ranked_notes.append((candidate, len(shared_topics), len(candidate_topics), shared_topics))

    ranked_notes.sort(key=lambda entry: (-entry[1], -entry[2], entry[0].title.lower()))

    unique_ranked_notes = {}
    for candidate, shared_count, topic_count, shared_topics in ranked_notes:
        if candidate.id in unique_ranked_notes:
            continue
        unique_ranked_notes[candidate.id] = (candidate, shared_count, topic_count, shared_topics)

    return RelatedKnowledgeResponse(
        related_topics=list(sorted(related_topics))[:5],
        related_notes=[
            RelatedKnowledgeNote(id=item.id, title=item.title, shared_topics=shared_topics)
            for item, _, _, shared_topics in list(unique_ranked_notes.values())[:limit]
        ],
    )
