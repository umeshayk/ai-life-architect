from __future__ import annotations

import json

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.topic import Topic
from app.models.topic_relationship import TopicRelationship
from app.services.topic_normalizer_service import canonical_topic_key


RELATIONSHIP_FALLBACK_EXPLANATIONS = {
    "related_to": "These topics frequently appear together in your knowledge graph.",
    "depends_on": "The source topic depends on the target topic as a prerequisite.",
    "used_in": "The target topic is used inside the source topic.",
    "subtopic_of": "The source topic is a subtopic of the target topic.",
}


def fallback_relationship_explanation(relationship_type: str) -> str:
    return RELATIONSHIP_FALLBACK_EXPLANATIONS.get(
        relationship_type,
        "These topics are connected in your knowledge graph."
    )


def relationship_source_badge(evidence: dict) -> str:
    return str((evidence or {}).get("source") or "rule")


def get_relationship_detail(db: Session, user_id: int, relationship_id: int) -> dict:
    relationship = db.scalar(
        select(TopicRelationship).where(
            TopicRelationship.id == relationship_id,
            TopicRelationship.user_id == user_id,
        )
    )
    if relationship is None:
        raise ValueError("Relationship not found")

    source_topic = relationship.source_topic
    target_topic = relationship.target_topic

    if relationship.source_topic_id:
        source_record = db.scalar(
            select(Topic.name).where(Topic.id == relationship.source_topic_id, Topic.user_id == user_id)
        )
        if source_record:
            source_topic = source_record
    if relationship.target_topic_id:
        target_record = db.scalar(
            select(Topic.name).where(Topic.id == relationship.target_topic_id, Topic.user_id == user_id)
        )
        if target_record:
            target_topic = target_record

    evidence = {}
    if relationship.evidence_json:
        try:
            evidence = json.loads(relationship.evidence_json)
        except json.JSONDecodeError:
            evidence = {}

    explanation = (relationship.explanation_text or "").strip() or fallback_relationship_explanation(relationship.relationship_type)

    return {
        "id": relationship.id,
        "source_topic": source_topic,
        "target_topic": target_topic,
        "relationship_type": relationship.relationship_type,
        "confidence": relationship.confidence,
        "explanation": explanation,
        "evidence": evidence,
    }


def resolve_topic_ids(db: Session, user_id: int, topic_names: list[str]) -> dict[str, int]:
    cleaned = [name for name in topic_names if canonical_topic_key(name)]
    if not cleaned:
        return {}

    rows = db.scalars(select(Topic).where(Topic.user_id == user_id)).all()
    topic_id_map: dict[str, int] = {}
    requested_keys = {canonical_topic_key(name) for name in cleaned}
    for row in rows:
        key = canonical_topic_key(row.name)
        if key in requested_keys and key not in topic_id_map:
            topic_id_map[key] = row.id
    return topic_id_map


def build_relationship_explanation(source_topic: str, target_topic: str, relationship_type: str) -> str:
    if relationship_type == "subtopic_of":
        return f"{source_topic} is a more specific concept within {target_topic}."
    if relationship_type == "used_in":
        return f"{target_topic} is used as part of {source_topic}."
    if relationship_type == "depends_on":
        return f"{source_topic} depends on {target_topic} as a prerequisite concept."
    return f"{source_topic} and {target_topic} frequently appear together in your knowledge graph."
