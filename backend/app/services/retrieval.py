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

GENERIC_RELATED_TOPICS = {
    "travel / spiritual",
    "ai systems",
    "business",
    "agriculture",
    "math",
    "technology",
}

GENERIC_CONCEPT_WORDS = {
    "accessible",
    "bus",
    "dedicated",
    "file",
    "first",
    "from",
    "itinerary",
    "located",
    "lord",
    "note",
    "notes",
    "nadu",
    "one",
    "pdf",
    "second",
    "third",
    "there",
    "temple",
    "temples",
    "train",
    "trip",
    "two",
    "via",
    "with",
}

IGNORED_CONCEPT_PHRASES = {
    "12 jyotirlinga temples",
    "accessible",
    "dedicated",
    "first",
    "located",
    "lord",
    "one",
    "there",
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
    related_topic_counts: dict[str, int] = {}
    current_topic_set = set(current_topics)
    current_specific_concepts = _extract_item_concepts(current_item)

    for candidate in candidates:
        candidate_topics = {
            content_topic.topic.name
            for content_topic in candidate.content_topics
            if content_topic.topic is not None and content_topic.topic.name.lower() not in IGNORED_RELATED_TOPICS
        }
        shared_topics = sorted(current_topic_set.intersection(candidate_topics))
        if not shared_topics:
            continue
        shared_specific_concepts = _rank_specific_shared_concepts(current_specific_concepts, candidate)
        display_shared_topics = shared_specific_concepts or [
            topic for topic in shared_topics if topic.lower() in GENERIC_RELATED_TOPICS
        ]
        for topic in (display_shared_topics or shared_topics):
            if topic and topic.lower() not in GENERIC_RELATED_TOPICS:
                related_topic_counts[topic] = related_topic_counts.get(topic, 0) + 1
        ranked_notes.append((candidate, len(shared_topics), len(candidate_topics), display_shared_topics))

    ranked_notes.sort(key=lambda entry: (-entry[1], -entry[2], entry[0].title.lower()))

    unique_ranked_notes = {}
    fallback_generic_counts: dict[str, int] = {}
    for candidate, shared_count, topic_count, display_shared_topics in ranked_notes:
        if candidate.id in unique_ranked_notes:
            continue
        ranked_shared_topics = display_shared_topics[:3]
        if not ranked_shared_topics:
            generic_topics = [
                content_topic.topic.name
                for content_topic in candidate.content_topics
                if content_topic.topic is not None and content_topic.topic.name.lower() in GENERIC_RELATED_TOPICS
            ]
            ranked_shared_topics = generic_topics[:3]
        for generic_topic in ranked_shared_topics:
            if generic_topic.lower() in GENERIC_RELATED_TOPICS:
                fallback_generic_counts[generic_topic] = fallback_generic_counts.get(generic_topic, 0) + 1
        unique_ranked_notes[candidate.id] = (candidate, shared_count, topic_count, ranked_shared_topics)

    ranked_topics = [
        topic
        for topic, _ in sorted(
            related_topic_counts.items(),
            key=lambda entry: (-entry[1], entry[0].lower()),
        )
        if topic and related_topic_counts.get(topic, 0) > 0
    ]
    if not ranked_topics:
        ranked_topics = [
            topic
            for topic, _ in sorted(
                fallback_generic_counts.items(),
                key=lambda entry: (-entry[1], entry[0].lower()),
            )
        ]

    return RelatedKnowledgeResponse(
        related_topics=ranked_topics[:5],
        related_notes=[
            RelatedKnowledgeNote(id=item.id, title=item.title, shared_topics=shared_topics)
            for item, _, _, shared_topics in list(unique_ranked_notes.values())[:limit]
        ],
    )


def _extract_item_concepts(item: KnowledgeItem) -> set[str]:
    concepts: set[str] = set()

    for content_topic in item.content_topics:
        if content_topic.topic is None:
            continue
        topic_name = content_topic.topic.name.strip()
        if (
            topic_name
            and topic_name.lower() not in IGNORED_RELATED_TOPICS
            and topic_name.lower() not in GENERIC_RELATED_TOPICS
        ):
            concepts.add(topic_name)

    for tag in (item.tags or "").split(","):
        cleaned = _normalize_concept(tag)
        if cleaned:
            concepts.add(cleaned)

    title = item.title or ""
    for segment in title.replace("_", " ").split("-"):
        cleaned = _normalize_concept(segment)
        if cleaned:
            concepts.add(cleaned)

    return concepts


def _rank_specific_shared_concepts(current_concepts: set[str], candidate: KnowledgeItem) -> list[str]:
    candidate_concepts = _extract_item_concepts(candidate)
    shared_specific_concepts = sorted(current_concepts.intersection(candidate_concepts))
    if shared_specific_concepts:
        return shared_specific_concepts

    # If topic overlap is only broad, surface the candidate's strongest title-derived concepts.
    preferred_candidate_concepts = [
        concept
        for concept in _extract_title_concepts(candidate.title)
        if concept and concept not in current_concepts and concept.lower() not in GENERIC_RELATED_TOPICS
    ]
    deduped_concepts: list[str] = []
    seen: set[str] = set()
    for concept in preferred_candidate_concepts:
        normalized = concept.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        deduped_concepts.append(concept)
    return deduped_concepts


def _extract_title_concepts(title: str | None) -> list[str]:
    concepts: list[str] = []
    for segment in (title or "").replace("_", " ").split("-"):
        cleaned = _normalize_concept(segment)
        if cleaned:
            concepts.append(cleaned)
    return concepts


def _extract_tag_concepts(tags: str | None) -> list[str]:
    concepts: list[str] = []
    for tag in (tags or "").split(","):
        cleaned = _normalize_concept(tag)
        if cleaned:
            concepts.append(cleaned)
    return concepts


def _normalize_concept(value: str) -> str:
    cleaned = " ".join(part for part in value.replace("_", " ").split() if part).strip()
    if not cleaned:
        return ""

    while cleaned and cleaned.split()[0].isdigit():
        parts = cleaned.split()
        cleaned = " ".join(parts[1:]).strip()
        if not cleaned:
            return ""

    lowered = cleaned.lower()
    if lowered in IGNORED_RELATED_TOPICS or lowered in GENERIC_RELATED_TOPICS or lowered in IGNORED_CONCEPT_PHRASES:
        return ""

    words = [word for word in cleaned.split() if word.lower() not in GENERIC_CONCEPT_WORDS]
    if not words:
        return ""

    normalized = " ".join(word.upper() if word.lower() in {"ai", "llm", "rag", "bm25"} else word.title() for word in words)
    if normalized.lower() in IGNORED_CONCEPT_PHRASES:
        return ""
    if len(normalized.split()) > 4:
        return ""
    return normalized
