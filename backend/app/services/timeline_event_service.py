from __future__ import annotations

import json
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

from app.models.content_topic import ContentTopic
from app.models.knowledge_event import KnowledgeEvent
from app.models.topic import Topic
from app.models.topic_mastery import TopicMastery
from app.services.learning_path_config import LEARNING_PATHS


VALID_RANGES = {"7d", "30d", "all"}


def _range_start(range_key: str) -> datetime | None:
    now = datetime.now(UTC)
    if range_key == "7d":
        return now - timedelta(days=7)
    if range_key == "30d":
        return now - timedelta(days=30)
    return None


def _serialize_metadata(value: dict[str, Any] | None) -> str:
    return json.dumps(value or {}, sort_keys=True)


def _deserialize_metadata(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        payload = json.loads(value)
        return payload if isinstance(payload, dict) else {}
    except json.JSONDecodeError:
        return {}


def _path_names_for_topic(topic_name: str) -> list[str]:
    lowered = (topic_name or "").strip().lower()
    results: list[str] = []
    for path in LEARNING_PATHS:
        if any((path_topic or "").strip().lower() == lowered for path_topic in path.get("topics", [])):
            results.append(path["path_name"])
    return results


def log_knowledge_event(
    db: Session,
    *,
    user_id: int,
    event_type: str,
    topic_id: int | None = None,
    related_topic_id: int | None = None,
    source: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> KnowledgeEvent:
    event = KnowledgeEvent(
        user_id=user_id,
        event_type=event_type,
        topic_id=topic_id,
        related_topic_id=related_topic_id,
        source=source,
        metadata_json=_serialize_metadata(metadata),
    )
    db.add(event)
    db.flush()
    return event


def build_topic_path_events(db: Session, *, user_id: int, topic: Topic, source: str | None = None) -> None:
    for path_name in _path_names_for_topic(topic.name):
        log_knowledge_event(
            db,
            user_id=user_id,
            event_type="topic_added_to_path",
            topic_id=topic.id,
            source=source or "path",
            metadata={"path_name": path_name},
        )


def _backfill_topic_events(db: Session, user_id: int) -> None:
    topics = db.scalars(
        select(Topic)
        .where(Topic.user_id == user_id)
        .order_by(Topic.created_at.asc(), Topic.id.asc())
    ).all()

    for topic in topics:
        db.add(
            KnowledgeEvent(
                user_id=user_id,
                event_type="topic_created",
                topic_id=topic.id,
                source="backfill",
                metadata_json=_serialize_metadata({"topic_name": topic.name}),
                created_at=topic.created_at,
            )
        )
        for path_name in _path_names_for_topic(topic.name):
            db.add(
                KnowledgeEvent(
                    user_id=user_id,
                    event_type="topic_added_to_path",
                    topic_id=topic.id,
                    source="backfill",
                    metadata_json=_serialize_metadata({"path_name": path_name}),
                    created_at=topic.created_at,
                )
            )


def _backfill_topic_links(db: Session, user_id: int) -> None:
    links = db.scalars(
        select(ContentTopic)
        .options(selectinload(ContentTopic.topic), selectinload(ContentTopic.knowledge_item))
        .where(ContentTopic.user_id == user_id)
        .order_by(ContentTopic.created_at.asc(), ContentTopic.id.asc())
    ).all()

    for link in links:
        topic = link.topic
        item = link.knowledge_item
        if topic is None or item is None:
            continue
        db.add(
            KnowledgeEvent(
                user_id=user_id,
                event_type="topic_linked",
                topic_id=topic.id,
                source="backfill",
                metadata_json=_serialize_metadata(
                    {
                        "item_id": item.id,
                        "item_title": item.title,
                        "confidence": link.confidence_score,
                    }
                ),
                created_at=link.created_at,
            )
        )


def _backfill_mastery_events(db: Session, user_id: int) -> None:
    mastery_rows = db.scalars(
        select(TopicMastery)
        .options(selectinload(TopicMastery.topic))
        .where(TopicMastery.user_id == user_id)
        .order_by(TopicMastery.last_updated.asc(), TopicMastery.id.asc())
    ).all()

    for mastery in mastery_rows:
        if mastery.topic is None:
            continue
        db.add(
            KnowledgeEvent(
                user_id=user_id,
                event_type="topic_mastery_updated",
                topic_id=mastery.topic_id,
                source="backfill",
                metadata_json=_serialize_metadata(
                    {
                        "topic_name": mastery.topic.name,
                        "mastery_score": mastery.mastery_score,
                    }
                ),
                created_at=mastery.last_updated,
            )
        )


def ensure_knowledge_events_seeded(db: Session, user_id: int) -> None:
    existing_event_id = db.scalar(select(KnowledgeEvent.id).where(KnowledgeEvent.user_id == user_id).limit(1))
    if existing_event_id is not None:
        return

    _backfill_topic_events(db, user_id)
    _backfill_topic_links(db, user_id)
    _backfill_mastery_events(db, user_id)
    db.commit()


def list_knowledge_events(db: Session, user_id: int, range_key: str = "30d") -> list[KnowledgeEvent]:
    ensure_knowledge_events_seeded(db, user_id)
    normalized_range = range_key if range_key in VALID_RANGES else "30d"
    stmt = (
        select(KnowledgeEvent)
        .options(selectinload(KnowledgeEvent.topic), selectinload(KnowledgeEvent.related_topic))
        .where(KnowledgeEvent.user_id == user_id)
        .order_by(desc(KnowledgeEvent.created_at), desc(KnowledgeEvent.id))
    )
    since = _range_start(normalized_range)
    if since is not None:
        stmt = stmt.where(KnowledgeEvent.created_at >= since)
    return db.scalars(stmt).all()


def event_label(event_type: str) -> str:
    return {
        "topic_created": "Topic Created",
        "topic_linked": "Topic Linked",
        "topic_expanded": "Topic Expanded",
        "topic_added_to_path": "Added To Path",
        "topic_mastery_updated": "Mastery Updated",
    }.get(event_type, event_type.replace("_", " ").title())


def serialize_event(event: KnowledgeEvent) -> dict[str, Any]:
    metadata = _deserialize_metadata(event.metadata_json)
    return {
        "id": event.id,
        "event_type": event.event_type,
        "event_label": event_label(event.event_type),
        "topic": event.topic.name if event.topic else metadata.get("topic_name"),
        "related_topic": event.related_topic.name if event.related_topic else metadata.get("related_topic_name"),
        "source": event.source or metadata.get("source") or "system",
        "metadata": metadata,
        "created_at": event.created_at,
    }


def build_event_groups(events: list[KnowledgeEvent]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        payload = serialize_event(event)
        date_key = event.created_at.astimezone(UTC).strftime("%Y-%m-%d")
        grouped[date_key].append(payload)

    results: list[dict[str, Any]] = []
    for date_key in sorted(grouped.keys(), reverse=True):
        results.append(
            {
                "date_key": date_key,
                "label": datetime.strptime(date_key, "%Y-%m-%d").strftime("%b %d, %Y"),
                "count": len(grouped[date_key]),
                "events": grouped[date_key],
            }
        )
    return results
