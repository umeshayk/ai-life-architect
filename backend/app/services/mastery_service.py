from __future__ import annotations

import json
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.content_topic import ContentTopic
from app.models.topic import Topic
from app.models.topic_mastery import TopicMastery
from app.models.topic_relationship import TopicRelationship
from app.services.learning_path_service import LEARNING_PATHS
from app.services.topic_normalizer_service import canonical_topic_key
from app.services.topic_summary_service import get_topic_summary

TOPIC_VIEW_WEIGHT = 0.18
LINKED_NOTE_WEIGHT = 0.28
RELATED_TOPIC_WEIGHT = 0.18
MENTOR_WEIGHT = 0.18
SUMMARY_WEIGHT = 0.08
PATH_WEIGHT = 0.10


def _deserialize_signals(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        payload = json.loads(value)
        return payload if isinstance(payload, dict) else {}
    except json.JSONDecodeError:
        return {}


def _serialize_signals(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True)


def _ensure_mastery_record(db: Session, user_id: int, topic_id: int) -> TopicMastery:
    record = db.scalar(
        select(TopicMastery).where(TopicMastery.user_id == user_id, TopicMastery.topic_id == topic_id)
    )
    if record is not None:
        return record
    record = TopicMastery(user_id=user_id, topic_id=topic_id, mastery_score=0.0, signals_json='{}')
    db.add(record)
    db.flush()
    return record


def _learning_paths_for_topic(topic_name: str) -> list[str]:
    normalized = canonical_topic_key(topic_name)
    path_names: list[str] = []
    for path in LEARNING_PATHS:
        if any(canonical_topic_key(item) == normalized for item in path.get('topics', [])):
            path_names.append(path['path_name'])
    return path_names


def _linked_note_count(db: Session, user_id: int, topic_id: int) -> int:
    return int(db.scalar(
        select(func.count(ContentTopic.id)).where(ContentTopic.user_id == user_id, ContentTopic.topic_id == topic_id)
    ) or 0)


def _related_topic_count(db: Session, user_id: int, topic_id: int) -> int:
    source_count = db.scalar(
        select(func.count(func.distinct(TopicRelationship.target_topic_id))).where(
            TopicRelationship.user_id == user_id,
            TopicRelationship.source_topic_id == topic_id,
            TopicRelationship.target_topic_id.is_not(None),
        )
    ) or 0
    target_count = db.scalar(
        select(func.count(func.distinct(TopicRelationship.source_topic_id))).where(
            TopicRelationship.user_id == user_id,
            TopicRelationship.target_topic_id == topic_id,
            TopicRelationship.source_topic_id.is_not(None),
        )
    ) or 0
    return int(source_count + target_count)


def _summary_ready(db: Session, user_id: int, topic_id: int) -> bool:
    try:
        summary = get_topic_summary(db, user_id, topic_id, refresh=False)
        return bool(summary.get('summary'))
    except Exception:
        return False


def _compute_mastery_score(signals: dict[str, Any]) -> float:
    topic_views = min(int(signals.get('topic_views', 0)) / 8, 1.0)
    linked_notes = min(int(signals.get('linked_notes', 0)) / 10, 1.0)
    related_topics = min(int(signals.get('related_topics_explored', 0)) / 8, 1.0)
    mentor_interactions = min(int(signals.get('mentor_interactions', 0)) / 4, 1.0)
    summary_ready = 1.0 if signals.get('has_summary') else 0.0
    path_count = min(len(signals.get('learning_paths', [])) / 2, 1.0)

    score = (
        topic_views * TOPIC_VIEW_WEIGHT
        + linked_notes * LINKED_NOTE_WEIGHT
        + related_topics * RELATED_TOPIC_WEIGHT
        + mentor_interactions * MENTOR_WEIGHT
        + summary_ready * SUMMARY_WEIGHT
        + path_count * PATH_WEIGHT
    )

    if mentor_interactions == 0 and linked_notes < 0.6:
        score = min(score, 0.78)

    return round(min(0.96, max(0.0, score)), 2)


def _build_signals(db: Session, user_id: int, topic: Topic, existing: dict[str, Any], increment_view: bool = False) -> dict[str, Any]:
    signals = dict(existing)
    signals['topic_views'] = int(signals.get('topic_views', 0)) + (1 if increment_view else 0)
    signals['mentor_interactions'] = int(signals.get('mentor_interactions', 0))
    signals['linked_notes'] = _linked_note_count(db, user_id, topic.id)
    signals['related_topics_explored'] = _related_topic_count(db, user_id, topic.id)
    signals['learning_paths'] = _learning_paths_for_topic(topic.name)
    signals['has_summary'] = _summary_ready(db, user_id, topic.id)
    return signals


def get_topic_mastery(db: Session, user_id: int, topic_id: int, track_view: bool = True) -> dict[str, Any]:
    topic = db.scalar(select(Topic).where(Topic.id == topic_id, Topic.user_id == user_id))
    if topic is None:
        raise ValueError('Topic not found')

    record = _ensure_mastery_record(db, user_id, topic.id)
    existing_signals = _deserialize_signals(record.signals_json)
    signals = _build_signals(db, user_id, topic, existing_signals, increment_view=track_view)
    record.signals_json = _serialize_signals(signals)
    record.mastery_score = _compute_mastery_score(signals)
    db.commit()
    db.refresh(record)

    return {
        'topic': topic.name,
        'topic_id': topic.id,
        'mastery_score': record.mastery_score,
        'signals': signals,
        'last_updated': record.last_updated,
    }


def record_mentor_interaction(db: Session, user_id: int, topic_name: str | None) -> None:
    if not topic_name:
        return
    topic = db.scalar(
        select(Topic).where(Topic.user_id == user_id, func.lower(Topic.name) == topic_name.strip().lower())
    )
    if topic is None:
        return

    record = _ensure_mastery_record(db, user_id, topic.id)
    signals = _deserialize_signals(record.signals_json)
    signals['mentor_interactions'] = int(signals.get('mentor_interactions', 0)) + 1
    signals = _build_signals(db, user_id, topic, signals, increment_view=False)
    record.signals_json = _serialize_signals(signals)
    record.mastery_score = _compute_mastery_score(signals)
    db.commit()


def get_mastery_lookup(db: Session, user_id: int) -> dict[str, float]:
    topics = db.scalars(select(Topic).where(Topic.user_id == user_id)).all()
    topic_by_id = {topic.id: topic for topic in topics}
    records = db.scalars(select(TopicMastery).where(TopicMastery.user_id == user_id)).all()
    lookup: dict[str, float] = {}
    for record in records:
        topic = topic_by_id.get(record.topic_id)
        if not topic:
            continue
        key = canonical_topic_key(topic.name)
        if key:
            lookup[key] = float(record.mastery_score or 0.0)
    return lookup
