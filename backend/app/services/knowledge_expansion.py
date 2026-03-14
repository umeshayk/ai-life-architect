from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.topic import Topic


CURATED_TOPIC_RELATIONSHIPS = {
    "Hybrid Search": [
        "BM25",
        "ANN Index",
        "Reranking",
        "Cross Encoder",
        "Query Expansion",
    ],
    "Semantic Search": [
        "Embeddings",
        "Vector Databases",
        "Approximate Nearest Neighbor",
        "Similarity Search",
    ],
    "Vector Databases": [
        "ANN Index",
        "HNSW",
        "IVF",
        "Vector Compression",
    ],
    "Embeddings": [
        "Similarity Search",
        "Cross Encoder",
        "Query Expansion",
    ],
}


def suggest_related_topics(db: Session, user_id: int, topic_name: str) -> list[str]:
    normalized_topic = (topic_name or "").strip()
    if not normalized_topic:
        return []

    curated = CURATED_TOPIC_RELATIONSHIPS.get(normalized_topic, [])
    if not curated:
        return []

    existing_topics = {
        (name or "").strip().lower()
        for name in db.scalars(
            select(Topic.name).where(Topic.user_id == user_id)
        ).all()
        if (name or "").strip()
    }

    suggestions: list[str] = []
    seen: set[str] = set()
    for suggestion in curated:
        normalized_suggestion = suggestion.strip().lower()
        if not normalized_suggestion or normalized_suggestion in existing_topics or normalized_suggestion in seen:
            continue
        seen.add(normalized_suggestion)
        suggestions.append(suggestion)
    return suggestions
