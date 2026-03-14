import json
from itertools import combinations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.content_topic import ContentTopic
from app.models.knowledge import KnowledgeItem
from app.models.topic_relationship import TopicRelationship
from app.services.relationship_service import build_relationship_explanation, resolve_topic_ids
from app.services.topic_normalizer_service import canonical_topic_key


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


def _classify_relationship(left: str, right: str) -> tuple[str, str, str, float, str]:
    left_lower = left.lower()
    right_lower = right.lower()
    left_tokens = set(_normalize_tokens(left))
    right_tokens = set(_normalize_tokens(right))
    overlap = left_tokens & right_tokens

    if left_lower != right_lower and left_lower in right_lower:
        return right, left, "subtopic_of", 0.84, "name_contains_topic"
    if left_lower != right_lower and right_lower in left_lower:
        return left, right, "subtopic_of", 0.84, "name_contains_topic"

    if overlap:
        preferred = left if len(left_tokens) >= len(right_tokens) else right
        secondary = right if preferred == left else left
        return preferred, secondary, "related_to", 0.72, "shared_topic_tokens"

    ordered = sorted((left, right), key=str.lower)
    return ordered[0], ordered[1], "related_to", 0.46, "same_document_cooccurrence"


def link_topics_for_item(
    db: Session,
    user_id: int,
    topic_names: list[str],
    *,
    item_id: int | None = None,
    item_name: str | None = None,
    source_method: str = "upload",
) -> int:
    ordered_topics: list[str] = []
    seen: set[str] = set()
    for name in topic_names:
        normalized = (name or "").strip()
        key = normalized.lower()
        if not normalized or key in seen:
            continue
        seen.add(key)
        ordered_topics.append(normalized)

    topic_id_map = resolve_topic_ids(db, user_id, ordered_topics)
    relationships_created = 0
    for left, right in combinations(ordered_topics, 2):
        source_topic, target_topic, relationship_type, confidence, rule_name = _classify_relationship(left, right)
        existing = db.scalar(
            select(TopicRelationship).where(
                TopicRelationship.user_id == user_id,
                TopicRelationship.source_topic == source_topic,
                TopicRelationship.target_topic == target_topic,
                TopicRelationship.relationship_type == relationship_type,
            )
        )

        evidence = {
            "source": source_method,
            "items": [item_name] if item_name else [],
            "item_ids": [item_id] if item_id is not None else [],
            "rule": rule_name,
        }
        explanation = build_relationship_explanation(source_topic, target_topic, relationship_type)
        source_topic_id = topic_id_map.get(canonical_topic_key(source_topic))
        target_topic_id = topic_id_map.get(canonical_topic_key(target_topic))

        if existing is not None:
            if confidence > existing.confidence:
                existing.confidence = confidence
            existing.source_topic_id = existing.source_topic_id or source_topic_id
            existing.target_topic_id = existing.target_topic_id or target_topic_id
            existing.explanation_text = existing.explanation_text or explanation
            try:
                current_evidence = json.loads(existing.evidence_json or "{}") if existing.evidence_json else {}
            except json.JSONDecodeError:
                current_evidence = {}
            merged_items = list(dict.fromkeys([*(current_evidence.get("items") or []), *evidence["items"]]))
            merged_item_ids = list(dict.fromkeys([*(current_evidence.get("item_ids") or []), *evidence["item_ids"]]))
            current_evidence.update(evidence)
            current_evidence["items"] = merged_items
            current_evidence["item_ids"] = merged_item_ids
            existing.evidence_json = json.dumps(current_evidence)
            continue

        db.add(
            TopicRelationship(
                user_id=user_id,
                source_topic_id=source_topic_id,
                target_topic_id=target_topic_id,
                source_topic=source_topic,
                target_topic=target_topic,
                relationship_type=relationship_type,
                confidence=confidence,
                evidence_json=json.dumps(evidence),
                explanation_text=explanation,
            )
        )
        relationships_created += 1

    if relationships_created:
        db.commit()
    else:
        db.flush()

    return relationships_created



def sync_relationships_for_user(db: Session, user_id: int, limit_items: int = 120) -> int:
    items = db.scalars(
        select(KnowledgeItem)
        .options(selectinload(KnowledgeItem.content_topics).selectinload(ContentTopic.topic))
        .where(KnowledgeItem.user_id == user_id)
        .order_by(KnowledgeItem.updated_at.desc())
        .limit(limit_items)
    ).all()

    created_total = 0
    for item in items:
        topic_names = sorted(
            {
                content_topic.topic.name
                for content_topic in item.content_topics
                if content_topic.topic is not None and content_topic.topic.name
            }
        )
        if len(topic_names) < 2:
            continue
        created_total += link_topics_for_item(
            db,
            user_id,
            topic_names,
            item_id=item.id,
            item_name=item.file_name or item.title,
            source_method="upload",
        )

    return created_total
