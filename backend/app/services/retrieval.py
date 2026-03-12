from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.content_topic import ContentTopic
from app.models.embedding import KnowledgeEmbedding
from app.models.knowledge import KnowledgeItem
from app.services.embeddings import ensure_user_embeddings, generate_embedding


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
