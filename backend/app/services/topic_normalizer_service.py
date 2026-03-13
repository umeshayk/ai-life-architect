import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.content_topic import ContentTopic
from app.models.topic import Topic


NOISE_WORDS = {
    "at",
    "attached",
    "face",
    "for",
    "in",
    "near",
    "opp",
    "opposite",
    "road",
    "sale",
    "site",
    "stage",
    "the",
}

DIRECTIONAL_WORDS = {
    "east",
    "north",
    "south",
    "west",
}

WEAK_DESCRIPTOR_WORDS = {
    "accessible",
    "agricultural",
    "attached",
    "commercial",
    "dedicated",
    "dristi",
    "enclave",
    "face",
    "first",
    "land",
    "muda",
    "old",
    "opp",
    "opposite",
    "property",
    "road",
    "sale",
    "site",
    "south",
    "stage",
    "then",
    "train",
    "trend",
    "verify",
    "west",
}

PROPERTY_CONTEXT_WORDS = {
    "apartment",
    "commercial",
    "estate",
    "flat",
    "house",
    "land",
    "muda",
    "plot",
    "project",
    "property",
    "residential",
    "sale",
    "site",
    "stage",
    "villa",
}

DOMAIN_WORDS = {
    "agriculture",
    "farm",
    "farming",
    "land",
    "property",
}

PRESERVED_LABELS = {
    "ai technology": "AI / Technology",
    "travel spiritual": "Travel / Spiritual",
}

DISPLAY_WORDS = {
    "ai": "AI",
    "api": "API",
    "bm25": "BM25",
    "llm": "LLM",
    "muda": "MUDA",
    "rag": "RAG",
}


def _clean_words(value: str) -> list[str]:
    normalized = re.sub(r"[^a-z0-9\s]+", " ", value.lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()
    if not normalized:
        return []
    words: list[str] = []
    seen: set[str] = set()
    for word in normalized.split():
        if word in seen:
            continue
        seen.add(word)
        words.append(word)
    return words


def _title_case(words: list[str]) -> str:
    return " ".join(DISPLAY_WORDS.get(word, word.title()) for word in words if word)


def normalize_topic_label(value: str) -> str:
    words = _clean_words(value)
    if not words:
        return ""

    preserved = PRESERVED_LABELS.get(" ".join(words))
    if preserved:
        return preserved

    property_context = any(word in PROPERTY_CONTEXT_WORDS for word in words)
    filtered = [word for word in words if word not in NOISE_WORDS and word != "muda"]

    if not filtered:
        filtered = [word for word in words if word not in {"muda"}]
    if not filtered:
        return ""

    if property_context:
        location_words = [
            word
            for word in filtered
            if word not in PROPERTY_CONTEXT_WORDS
            and word not in DOMAIN_WORDS
            and word not in DIRECTIONAL_WORDS
            and word not in WEAK_DESCRIPTOR_WORDS
        ]
        if not location_words:
            location_words = [
                word
                for word in filtered
                if word not in PROPERTY_CONTEXT_WORDS
                and word not in DOMAIN_WORDS
                and word not in DIRECTIONAL_WORDS
                and len(word) >= 5
            ]
        if location_words:
            return f"{_title_case(location_words[:2])} Property"
        fallback_words = [
            word
            for word in filtered
            if word not in DIRECTIONAL_WORDS and word not in {"property", "sale", "site"}
        ]
        if fallback_words:
            return _title_case(fallback_words[: min(3, len(fallback_words))])
        return ""

    if len(filtered) > 4:
        filtered = filtered[:4]

    return _title_case(filtered)


def canonical_topic_key(value: str) -> str:
    normalized = normalize_topic_label(value)
    return re.sub(r"\s+", " ", normalized.lower()).strip()


def topics_are_similar(left: str, right: str) -> bool:
    left_key = canonical_topic_key(left)
    right_key = canonical_topic_key(right)
    if not left_key or not right_key:
        return False
    if left_key == right_key:
        return True

    left_tokens = set(left_key.split())
    right_tokens = set(right_key.split())
    if not left_tokens or not right_tokens:
        return False

    overlap = len(left_tokens & right_tokens)
    minimum = min(len(left_tokens), len(right_tokens))
    return overlap >= minimum and minimum >= 2


def find_similar_topic(db: Session, user_id: int, topic_name: str) -> Topic | None:
    topic_key = canonical_topic_key(topic_name)
    if not topic_key:
        return None

    topics = db.scalars(select(Topic).where(Topic.user_id == user_id)).all()
    for topic in topics:
        if topics_are_similar(topic.name, topic_name):
            return topic
    return None


def get_or_create_normalized_topic(db: Session, user_id: int, topic_name: str) -> tuple[Topic | None, bool]:
    normalized_name = normalize_topic_label(topic_name)
    if not normalized_name:
        return None, False

    existing = find_similar_topic(db, user_id, normalized_name)
    if existing is not None:
        canonical_name = normalize_topic_label(existing.name)
        if canonical_name and existing.name != canonical_name:
            existing.name = canonical_name
            db.flush()
        return existing, False

    topic = Topic(user_id=user_id, name=normalized_name)
    db.add(topic)
    db.flush()
    return topic, True


def merge_similar_topics(db: Session, user_id: int) -> int:
    topics = db.scalars(
        select(Topic).where(Topic.user_id == user_id).order_by(Topic.id.asc())
    ).all()
    canonical_topics: dict[str, Topic] = {}
    merged_topics = 0

    for topic in topics:
        canonical_name = normalize_topic_label(topic.name)
        if not canonical_name:
            continue

        topic_key = canonical_topic_key(canonical_name)
        current = canonical_topics.get(topic_key)
        if current is None:
            if topic.name != canonical_name:
                topic.name = canonical_name
                db.flush()
            canonical_topics[topic_key] = topic
            continue

        links = db.scalars(
            select(ContentTopic).where(ContentTopic.topic_id == topic.id)
        ).all()
        existing_links = {
            row.knowledge_id: row
            for row in db.scalars(
                select(ContentTopic).where(ContentTopic.topic_id == current.id)
            ).all()
        }

        for link in links:
            existing = existing_links.get(link.knowledge_id)
            if existing is not None:
                existing.confidence_score = max(existing.confidence_score, link.confidence_score)
                db.delete(link)
                continue
            link.topic_id = current.id

        db.delete(topic)
        merged_topics += 1

    db.commit()
    return merged_topics
