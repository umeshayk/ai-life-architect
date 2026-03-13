from itertools import combinations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.topic_relationship import TopicRelationship


RELATIONSHIP_STOP_WORDS = {
    "a",
    "an",
    "and",
    "for",
    "in",
    "of",
    "on",
    "the",
    "to",
    "with",
}


def _normalize_tokens(value: str) -> list[str]:
    return [
        token
        for token in value.lower().replace("/", " ").replace("-", " ").split()
        if token and token not in RELATIONSHIP_STOP_WORDS
    ]


def _classify_relationship(left: str, right: str) -> tuple[str, str, str, float]:
    left_lower = left.lower()
    right_lower = right.lower()
    left_tokens = set(_normalize_tokens(left))
    right_tokens = set(_normalize_tokens(right))
    overlap = left_tokens & right_tokens

    if left_lower != right_lower and left_lower in right_lower:
        return right, left, "subtopic_of", 0.84
    if left_lower != right_lower and right_lower in left_lower:
        return left, right, "subtopic_of", 0.84

    if overlap:
        preferred = left if len(left_tokens) >= len(right_tokens) else right
        secondary = right if preferred == left else left
        return preferred, secondary, "related_to", 0.72

    ordered = sorted((left, right), key=str.lower)
    return ordered[0], ordered[1], "related_to", 0.46


def link_topics_for_item(db: Session, user_id: int, topic_names: list[str]) -> int:
    ordered_topics: list[str] = []
    seen: set[str] = set()
    for name in topic_names:
        normalized = (name or "").strip()
        key = normalized.lower()
        if not normalized or key in seen:
            continue
        seen.add(key)
        ordered_topics.append(normalized)

    relationships_created = 0
    for left, right in combinations(ordered_topics, 2):
        source_topic, target_topic, relationship_type, confidence = _classify_relationship(left, right)
        existing = db.scalar(
            select(TopicRelationship).where(
                TopicRelationship.user_id == user_id,
                TopicRelationship.source_topic == source_topic,
                TopicRelationship.target_topic == target_topic,
                TopicRelationship.relationship_type == relationship_type,
            )
        )
        if existing is not None:
            if confidence > existing.confidence:
                existing.confidence = confidence
            continue

        db.add(
            TopicRelationship(
                user_id=user_id,
                source_topic=source_topic,
                target_topic=target_topic,
                relationship_type=relationship_type,
                confidence=confidence,
            )
        )
        relationships_created += 1

    if relationships_created:
        db.commit()
    else:
        db.flush()

    return relationships_created
